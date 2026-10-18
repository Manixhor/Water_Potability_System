const form = document.querySelector('#sample-form');
const title = document.querySelector('#result-title');
const body = document.querySelector('#result-body');
const tag = document.querySelector('#result-tag');
const button = document.querySelector('#analyze');
const ORDER = ['ph', 'Hardness', 'Solids', 'Chloramines', 'Sulfate', 'Conductivity', 'Organic_carbon', 'Trihalomethanes', 'Turbidity'];
const LABELS = { ph: 'pH', Hardness: 'Hardness', Solids: 'Dissolved solids', Chloramines: 'Chloramines', Sulfate: 'Sulfate', Conductivity: 'Conductivity', Organic_carbon: 'Organic carbon', Trihalomethanes: 'Trihalomethanes', Turbidity: 'Turbidity' };
const BOUNDS = { ph: [0, 14], Hardness: [0, 1000], Solids: [0, 100000], Chloramines: [0, 50], Sulfate: [0, 2000], Conductivity: [0, 5000], Organic_carbon: [0, 100], Trihalomethanes: [0, 1000], Turbidity: [0, 100] };

// Browser-side forest runtime. The AQF1 asset is a direct typed-array view of the
// fitted scikit-learn pipeline (imputer medians + 500 decision trees), so parsing
// is instant and a prediction is a synchronous pointer walk — no WASM, no workers.
let forestPromise = null;
function loadForest() {
  if (!forestPromise) {
    forestPromise = (async () => {
      const response = await fetch('/static/water.forest');
      if (!response.ok) throw new Error('Model asset unavailable (' + response.status + ')');
      return parseForest(await response.arrayBuffer());
    })();
  }
  return forestPromise;
}
function parseForest(buffer) {
  const view = new DataView(buffer);
  const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
  if (magic !== 'AQF1' || view.getUint32(4, true) !== 1) throw new Error('Unsupported model asset');
  const nFeatures = view.getUint32(8, true);
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
  const x = Float64Array.from(raw);
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
async function checkHealth() {
  try {
    const response = await fetch('/health');
    if (!response.ok) throw new Error();
    const data = await response.json();
    const ready = data.model_ready;
    document.querySelector('#model-status').textContent = ready ? 'Model ready' : 'Training required';
  } catch {
    document.querySelector('#model-status').textContent = 'Service offline';
  }
}
checkHealth();
loadForest().catch(() => {});
document.querySelector('#example').addEventListener('click', () => {
  form.querySelectorAll('input').forEach(input => { input.value = input.dataset.example; });
  title.textContent = 'Example loaded';
  body.textContent = 'These illustrative measurements are for exploring the interface. They are not a verified laboratory sample.';
  tag.textContent = 'EXAMPLE SAMPLE';
});
document.querySelectorAll('.sample').forEach(sample => {
  sample.addEventListener('click', () => {
    const values = JSON.parse(sample.dataset.sample);
    form.querySelectorAll('input').forEach(input => { if (input.id in values) input.value = values[input.id]; });
    if (typeof form.requestSubmit === 'function') form.requestSubmit();
    else form.dispatchEvent(new Event('submit', { cancelable: true }));
    const result = document.querySelector('.result');
    if (result) result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
});
form.addEventListener('reset', () => {
  title.textContent = 'Ready for a fresh sample.';
  body.textContent = 'Enter all nine measurements to begin an assessment.';
  tag.textContent = 'AWAITING SAMPLE';
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  const raw = Object.fromEntries([...new FormData(form)]);
  const values = [];
  for (const key of ORDER) {
    const value = Number(raw[key]);
    const [low, high] = BOUNDS[key];
    if (!Number.isFinite(value) || value < low || value > high) {
      title.textContent = 'Assessment unavailable';
      body.textContent = `${LABELS[key]} must be a finite number between ${low} and ${high}.`;
      tag.textContent = 'ACTION REQUIRED';
      return;
    }
    values.push(value);
  }
  button.disabled = true;
  button.textContent = 'Assessing…';
  try {
    const prediction = forestPredict(await loadForest(), values);
    title.textContent = prediction ? 'Predicted potable' : 'Predicted non-potable';
    body.textContent = 'Research prediction only. This result does not certify that water is safe to drink.';
    tag.textContent = 'RESEARCH PREDICTION';
  } catch (error) {
    title.textContent = 'Assessment unavailable';
    body.textContent = error && error.message ? error.message : 'Assessment failed. Please try again.';
    tag.textContent = 'ACTION REQUIRED';
  } finally {
    button.disabled = false;
    button.textContent = 'Assess sample ↗';
  }
});
