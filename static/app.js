const form = document.querySelector('#sample-form');
const title = document.querySelector('#result-title');
const body = document.querySelector('#result-body');
const tag = document.querySelector('#result-tag');
const button = document.querySelector('#analyze');
const status = document.querySelector('#model-status');
const inputs = [...form.querySelectorAll('input')];
let revision = 0;
let busy = false;

function showResult(heading, message, badge) {
  title.textContent = heading;
  body.textContent = message;
  tag.textContent = badge;
}
async function fetchJSON(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(30000) });
  let data;
  try { data = await response.json(); }
  catch { throw new Error('The service returned an unexpected response. Please retry.'); }
  if (!response.ok) throw new Error(data.error || 'Assessment failed. Please retry.');
  return data;
}
async function checkHealth() {
  try {
    const ready = window.aquaModel ? await window.aquaModel.ready() : (await fetchJSON('/health')).model_ready;
    status.textContent = ready ? 'Model ready' : 'Training required';
  } catch { status.textContent = 'Model unavailable — retry assessment'; }
}
checkHealth();

function invalidate() {
  revision += 1;
  showResult('Sample updated', 'Assess your sample to see a prediction for these measurements.', 'AWAITING ASSESSMENT');
}
form.addEventListener('input', invalidate);
document.querySelector('#example').addEventListener('click', () => {
  revision += 1;
  inputs.forEach(input => { input.value = input.dataset.example; });
  showResult('Example loaded', 'These illustrative measurements are for exploring the interface. They are not a verified laboratory sample.', 'EXAMPLE SAMPLE');
});
document.querySelectorAll('.sample').forEach(sample => {
  sample.addEventListener('click', () => {
    if (busy) return;
    const values = JSON.parse(sample.dataset.sample);
    inputs.forEach(input => { if (input.id in values) input.value = values[input.id]; });
    revision += 1;
    form.requestSubmit();
    document.querySelector('.result').scrollIntoView({
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest'
    });
  });
});
form.addEventListener('reset', () => {
  revision += 1;
  showResult('Ready for a fresh sample.', 'Enter all nine measurements to begin an assessment.', 'AWAITING SAMPLE');
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (busy || !form.reportValidity()) return;
  const values = {};
  for (const input of inputs) {
    const value = input.valueAsNumber;
    if (!Number.isFinite(value) || value < Number(input.min) || value > Number(input.max)) {
      input.focus();
      showResult('Check your measurements', 'Enter a valid value for every field within its displayed range.', 'ACTION REQUIRED');
      return;
    }
    values[input.name] = value;
  }
  const submittedRevision = ++revision;
  busy = true;
  button.disabled = true;
  button.textContent = 'Assessing…';
  document.querySelectorAll('.sample').forEach(sample => { sample.disabled = true; });
  try {
    const data = window.aquaModel ? await window.aquaModel.predict(values) : await fetchJSON('/api/predict', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values)
    });
    status.textContent = 'Model ready';
    if (submittedRevision !== revision) return;
    showResult(data.label, data.notice, 'RESEARCH PREDICTION');
  } catch (error) {
    if (submittedRevision !== revision) return;
    const message = error.name === 'TimeoutError' ? 'The assessment timed out. Check your connection and retry.' : error.message;
    showResult('Assessment unavailable', message || 'Please try again.', 'ACTION REQUIRED');
    status.textContent = 'Assessment failed — retry';
  } finally {
    busy = false;
    button.disabled = false;
    button.textContent = 'Assess sample ↗';
    document.querySelectorAll('.sample').forEach(sample => { sample.disabled = false; });
  }
});
