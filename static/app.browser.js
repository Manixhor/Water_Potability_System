const ORDER = ['ph', 'Hardness', 'Solids', 'Chloramines', 'Sulfate', 'Conductivity', 'Organic_carbon', 'Trihalomethanes', 'Turbidity'];
// Browser-side forest runtime. The AQF1 asset is a direct typed-array view of the
// fitted scikit-learn pipeline (imputer medians + 500 decision trees), so parsing
// is instant and a prediction is a synchronous pointer walk — no WASM, no workers.
let forestPromise = null;
function loadForest() {
  if (!forestPromise) {
    forestPromise = (async () => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 30000);
      try {
        const response = await fetch('/static/water.forest', { signal: controller.signal });
        if (!response.ok) throw new Error('The model could not load. Check your connection and retry the assessment.');
        return parseForest(await response.arrayBuffer());
      } finally { clearTimeout(timer); }
    })().catch(error => { forestPromise = null; throw error; });
  }
  return forestPromise;
}
function parseForest(buffer) {
  if (buffer.byteLength < 56) throw new Error('Model asset is incomplete. Please retry.');
  const view = new DataView(buffer);
  const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
  if (magic !== 'AQF1' || view.getUint32(4, true) !== 1) throw new Error('Unsupported model asset');
  const nFeatures = view.getUint32(8, true);
  if (nFeatures !== ORDER.length) throw new Error('Model feature mismatch');
  const nTrees = view.getUint32(12, true);
  const nNodes = view.getUint32(16, true);
  const nLeaves = view.getUint32(20, true);
  const offset = index => view.getUint32(24 + index * 4, true);
  return {
    nFeatures,
    nTrees,
    fills: new Float64Array(buffer, offset(0), nFeatures),
    trees: new Uint32Array(buffer, offset(1), nTrees * 2),
    columns: new Int16Array(buffer, offset(2), nNodes),
    left: new Int32Array(buffer, offset(3), nNodes),
    right: new Int32Array(buffer, offset(4), nNodes),
    thresholds: new Float64Array(buffer, offset(5), nNodes),
    slots: new Int32Array(buffer, offset(6), nNodes),
    values: new Float64Array(buffer, offset(7), nLeaves * 2),
  };
}
function forestPredict(forest, raw) {
  const x = Float32Array.from(raw);
  for (let i = 0; i < x.length; i += 1) if (Number.isNaN(x[i])) x[i] = forest.fills[i];
  let potable = 0;
  let nonPotable = 0;
  for (let t = 0; t < forest.nTrees; t += 1) {
    let node = forest.trees[t * 2];
    for (;;) {
      const slot = forest.slots[node];
      if (slot >= 0) {
        nonPotable += forest.values[slot * 2];
        potable += forest.values[slot * 2 + 1];
        break;
      }
      node = x[forest.columns[node]] <= forest.thresholds[node] ? forest.left[node] : forest.right[node];
    }
  }
  return potable > nonPotable ? 1 : 0;
}

window.aquaModel = {
  ready: async () => { await loadForest(); return true; },
  predict: async values => {
    const prediction = forestPredict(await loadForest(), ORDER.map(key => values[key]));
    return { prediction, label: prediction ? 'Predicted potable' : 'Predicted non-potable',
      notice: 'Research prediction only. This result does not certify that water is safe to drink.' };
  },
};
