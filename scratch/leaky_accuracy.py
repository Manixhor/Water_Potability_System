"""Teaching demo: where an "87% accurate" water-potability model comes from.

This file is not part of the app and is never deployed. It prints the honest
score next to a ladder of common preprocessing mistakes that inflate it, so the
gap is visible rather than hand-waved. It only reads files; it writes nothing.

    python scratch/leaky_accuracy.py [path/to/water_potability.csv]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from features import FEATURES  # noqa: E402

FEATURES = list(FEATURES)
LABEL = "Potability"
SEED = 42
METRICS = REPO / "models" / "water.metrics.json"


def new_forest():
    """Same estimator the app ships, so only the order of steps changes."""
    return RandomForestClassifier(
        n_estimators=500, class_weight="balanced", random_state=SEED, n_jobs=-1
    )


def impute(frame, medians):
    """Fill missing values with the supplied per-feature medians."""
    out = frame.copy()
    out[FEATURES] = out[FEATURES].fillna(medians)
    return out


def evaluate(data, *, medians_from_full=False, oversample_first=False, copies=1):
    """Fit on a 70/30 split, varying how much of the test set training has seen."""
    if copies > 1:
        # "data augmentation": concatenating the frame with itself
        data = pd.concat([data] * copies, ignore_index=True)
    if oversample_first:
        # "class balancing": upsampling done before the split
        majority = data[data[LABEL] == 0]
        minority = data[data[LABEL] == 1]
        extra = minority.sample(len(majority) - len(minority), replace=True, random_state=SEED)
        data = pd.concat([majority, minority, extra], ignore_index=True)

    train, test = train_test_split(data, test_size=.3, stratify=data[LABEL], random_state=SEED)
    medians = data[FEATURES].median() if medians_from_full else train[FEATURES].median()
    train, test = impute(train, medians), impute(test, medians)

    model = new_forest().fit(train[FEATURES], train[LABEL])
    score = accuracy_score(test[LABEL], model.predict(test[FEATURES]))
    return score, len(train), len(test)


def evaluate_on_training_rows(data):
    """No holdout at all: score the model on the rows it just memorised."""
    full = impute(pd.concat([data] * 2, ignore_index=True), data[FEATURES].median())
    model = new_forest().fit(full[FEATURES], full[LABEL])
    score = accuracy_score(full[LABEL], model.predict(full[FEATURES]))
    return score, len(full), len(full)


def main():
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data" / "water_potability.csv"
    if not csv.exists():
        sys.exit(f"{csv} not found - this demo needs the dataset (it is not committed).")

    data = pd.read_csv(csv)
    data = data[[*FEATURES, LABEL]].apply(pd.to_numeric, errors="raise")

    steps = [
        ("honest: split first, impute from the training rows only", evaluate(data)),
        ("leak 1: impute medians from the whole dataset, then split", evaluate(data, medians_from_full=True)),
        ("leak 2: balance the classes before the split (oversample)", evaluate(data, oversample_first=True)),
        ("leak 3: duplicate every row once, then split  <- the '87%'", evaluate(data, copies=2)),
        ("leak 4: duplicate every row twice, then split", evaluate(data, copies=3)),
        ("leak 5: no holdout at all - score on the training rows", evaluate_on_training_rows(data)),
    ]

    print()
    print(f"dataset: {len(data)} rows, {data[LABEL].mean():.1%} potable")
    if METRICS.exists():
        reported = json.loads(METRICS.read_text())
        print(
            "shipped model (models/water.metrics.json): "
            f"accuracy {reported['accuracy']:.4f}, "
            f"balanced {reported['balanced_accuracy']:.4f}, "
            f"majority baseline {reported['majority_baseline']:.4f}"
        )
    print()
    print(f"{'pipeline':62s} {'accuracy':>9s} {'train':>7s} {'test':>7s}")
    for name, (score, train_size, test_size) in steps:
        print(f"{name:62s} {score:>8.4f} {train_size:>7d} {test_size:>7d}")
    print()
    print("Every row above uses the same forest. The only thing that changes is how")
    print("many test rows the model has already seen while training, so the last")
    print("four numbers measure memorisation, not water quality.")
    print()


if __name__ == "__main__":
    main()
