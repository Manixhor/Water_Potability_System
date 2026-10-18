"""Build the static Cloudflare Workers site into dist/.

Renders the Flask UI, exports the trained pipeline to a compact binary forest
(AQF1) that the browser evaluates directly, and verifies the export predicts
identically to the served scikit-learn model. Requires only requirements.txt.
"""
import shutil
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
sys.path.insert(0, str(ROOT))


def export_forest(model):
    """Serialize imputer medians + fitted forest as AQF1 bytes.

    Layout (all uint32 little-endian):
      0 magic 'AQF1' | 4 version | 8 nFeatures | 12 nTrees | 16 nNodes | 20 nLeaves
      24 eight offsets: fills, trees, columns, left, right, thresholds, slots, values
      56 body: each section 8-byte aligned so the browser can create typed-array
      views directly over the buffer (no parsing step).
    """
    from features import FEATURES

    fills = np.asarray(model.named_steps['simpleimputer'].statistics_, dtype=np.float64)
    if fills.shape != (len(FEATURES),) or np.isnan(fills).any():
        sys.exit('Expected finite imputer medians for all nine features.')

    classifier = model.named_steps['randomforestclassifier']
    columns, lefts, rights, thresholds, slots, values, bounds = [], [], [], [], [], [], []
    value_rows = base = 0
    for estimator in classifier.estimators_:
        tree = estimator.tree_
        count = int(tree.node_count)
        internal = tree.children_left != -1
        columns.append(np.where(internal, tree.feature, -1).astype('<i2'))
        left = tree.children_left.astype(np.int64) + base
        right = tree.children_right.astype(np.int64) + base
        left[~internal] = -1
        right[~internal] = -1
        lefts.append(left.astype('<i4'))
        rights.append(right.astype('<i4'))
        thresholds.append(tree.threshold.astype('<f8'))
        leaf_rows = np.flatnonzero(~internal)
        counts = tree.value[leaf_rows, 0, :].astype(np.float64)
        totals = counts.sum(axis=1, keepdims=True)
        leaf_values = np.divide(counts, totals, out=np.zeros_like(counts), where=totals != 0)
        slot = np.full(count, -1, dtype='<i4')
        slot[leaf_rows] = value_rows + np.arange(leaf_rows.size, dtype=np.int64)
        slots.append(slot)
        values.append(leaf_values.astype('<f8'))
        bounds.append((base, count))
        value_rows += leaf_rows.size
        base += count

    sections = [
        fills.astype('<f8'),
        np.asarray(bounds, dtype='<u4'),
        np.concatenate(columns),
        np.concatenate(lefts),
        np.concatenate(rights),
        np.concatenate(thresholds),
        np.concatenate(slots),
        np.concatenate(values),
    ]

    payload = bytearray(struct.pack(
        '<4sIIIII', b'AQF1', 1, len(FEATURES), len(classifier.estimators_), base, value_rows
    ))
    table_at = len(payload)
    payload.extend(b'\x00' * (8 * 4))
    offsets = []
    for section in sections:
        while len(payload) % 8:
            payload.append(0)
        offsets.append(len(payload))
        payload.extend(np.ascontiguousarray(section).tobytes())
    struct.pack_into('<8I', payload, table_at, *offsets)
    return bytes(payload)


def forest_predict(payload, x_raw):
    """Reference re-implementation of the browser traversal, run from the bytes."""
    n_features, n_trees, n_nodes, n_leaves = struct.unpack_from('<IIII', payload, 8)
    off = struct.unpack_from('<8I', payload, 24)
    fills = np.frombuffer(payload, dtype='<f8', count=n_features, offset=off[0])
    trees = np.frombuffer(payload, dtype='<u4', count=n_trees * 2, offset=off[1]).reshape(-1, 2)
    columns = np.frombuffer(payload, dtype='<i2', count=n_nodes, offset=off[2])
    left = np.frombuffer(payload, dtype='<i4', count=n_nodes, offset=off[3])
    right = np.frombuffer(payload, dtype='<i4', count=n_nodes, offset=off[4])
    thresholds = np.frombuffer(payload, dtype='<f8', count=n_nodes, offset=off[5])
    slots = np.frombuffer(payload, dtype='<i4', count=n_nodes, offset=off[6])
    values = np.frombuffer(payload, dtype='<f8', count=n_leaves * 2, offset=off[7]).reshape(-1, 2)

    x = np.array(x_raw, dtype=np.float64, copy=True)
    missing = np.isnan(x)
    if missing.any():
        x[missing] = np.take(fills, np.nonzero(missing)[1])
    scores = np.zeros((x.shape[0], 2))
    for start in trees[:, 0]:
        current = np.full(x.shape[0], int(start), dtype=np.int64)
        active = np.ones(x.shape[0], dtype=bool)
        while active.any():
            rows = np.flatnonzero(active)
            found = slots[current[rows]]
            resolved_mask = found >= 0
            resolved = rows[resolved_mask]
            scores[resolved] += values[found[resolved_mask]]
            active[resolved] = False
            moving = rows[~resolved_mask]
            if moving.size:
                nodes = current[moving]
                go_left = x[moving, columns[nodes]] <= thresholds[nodes]
                current[moving] = np.where(go_left, left[nodes], right[nodes])
    return (scores[:, 1] > scores[:, 0]).astype(np.int64)


def main():
    import joblib
    import pandas as pd

    from app import create_app
    from features import FEATURES, SAMPLES

    model_path = ROOT / 'models' / 'water.joblib'
    if not model_path.is_file():
        sys.exit('Missing models/water.joblib — train first: python train.py data/water_potability.csv')

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / 'static').mkdir(parents=True)

    # 1. Server-rendered index.html from the same Jinja template the Flask app uses.
    response = create_app().test_client().get('/')
    if response.status_code != 200:
        sys.exit(f'Rendering templates/index.html failed with {response.status_code}')
    (DIST / 'index.html').write_bytes(response.data)

    # 2. Export the pipeline and verify it predicts like the served model.
    model = joblib.load(model_path)
    payload = export_forest(model)
    (DIST / 'static' / 'water.forest').write_bytes(payload)
    agreement = None
    csv = ROOT / 'data' / 'water_potability.csv'
    if csv.is_file():
        data = pd.read_csv(csv)
        expected = model.predict(data[list(FEATURES)])
        predicted = forest_predict(payload, data[list(FEATURES)].to_numpy())
        agreement = float((expected == predicted).mean())
        if agreement < 0.999:
            sys.exit(f'Forest export parity {agreement:.4f} below 0.999 — refusing to build.')

    # 2b. Preset badges must carry the served model's own verdict, so the UI's
    # "Drinkable" / "Not drinkable" labels cannot drift from the predictions.
    for sample in SAMPLES:
        ordered = {key: sample['measurements'][key] for key in FEATURES}
        predicted = int(model.predict(pd.DataFrame([ordered]))[0])
        if predicted != int(bool(sample['drinkable'])):
            sys.exit(
                f"Sample '{sample['name']}' is labelled drinkable={sample['drinkable']} "
                f'but the model predicts {predicted} — refusing to build.'
            )

    # 3. Front-end assets: browser runtime served as /static/app.js.
    shutil.copy(ROOT / 'static' / 'style.css', DIST / 'static' / 'style.css')
    shutil.copy(ROOT / 'static' / 'app.browser.js', DIST / 'static' / 'app.js')
    shutil.copy(ROOT / 'cloudflare' / '_headers', DIST / '_headers')

    parity = f', parity {agreement:.2%}' if agreement is not None else ', parity skipped (no data CSV)'
    print(f'dist/ ready — water.forest {len(payload) / 1048576:.1f} MiB{parity}')


if __name__ == '__main__':
    main()
