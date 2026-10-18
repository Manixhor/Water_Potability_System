const form = document.querySelector('#sample-form');
const title = document.querySelector('#result-title');
const body = document.querySelector('#result-body');
const tag = document.querySelector('#result-tag');
const button = document.querySelector('#analyze');
const modelStatus = document.querySelector('#model-status');
const resultPanel = document.querySelector('.result');
const retry = document.querySelector('#retry');
const inputs = [...form.querySelectorAll('input')];
let revision = 0;
let busy = false;

function showResult(heading, message, badge) {
  title.textContent = heading;
  body.textContent = message;
  tag.textContent = badge;
  retry.hidden = badge !== 'ACTION REQUIRED';
  resultPanel.dataset.state = badge === 'RESEARCH PREDICTION' ? 'complete' : badge === 'ACTION REQUIRED' ? 'error' : 'pending';
}
function revealResult() {
  const heading = title.getBoundingClientRect();
  // Leave the page still when the result and its message are already in view.
  if (heading.top >= 16 && heading.bottom + 80 <= window.innerHeight) return;
  const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  resultPanel.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
}
function submitSample() {
  if (typeof form.requestSubmit === 'function') form.requestSubmit();
  else form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}
retry.addEventListener('click', submitSample);
async function fetchJSON(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    let data;
    try { data = await response.json(); }
    catch { throw new Error('The service returned an unexpected response. Please retry.'); }
    if (!response.ok) throw new Error(data.error || 'Assessment failed. Please retry.');
    return data;
  } finally { clearTimeout(timer); }
}
async function checkHealth() {
  try {
    const ready = window.aquaModel ? await window.aquaModel.ready() : (await fetchJSON('/health')).model_ready;
    modelStatus.textContent = ready ? 'Model ready' : 'Training required';
  } catch { modelStatus.textContent = 'Model unavailable — retry assessment'; }
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
    submitSample();
  });
});
form.addEventListener('reset', () => {
  revision += 1;
  showResult('Ready for a fresh sample.', 'Enter all nine measurements to begin an assessment.', 'AWAITING SAMPLE');
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  if (!form.reportValidity()) {
    showResult('Check your measurements', 'Enter all nine measurements within their displayed ranges, then assess the sample again.', 'CHECK INPUTS');
    return;
  }
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
  resultPanel.setAttribute('aria-busy', 'true');
  showResult('Assessing your sample…', 'Loading the model and checking your measurements. This may take a few seconds on the first assessment.', 'ASSESSING');
  revealResult();
  document.querySelectorAll('.sample').forEach(sample => { sample.disabled = true; });
  try {
    const data = window.aquaModel ? await window.aquaModel.predict(values) : await fetchJSON('/api/predict', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values)
    });
    modelStatus.textContent = 'Model ready';
    if (submittedRevision !== revision) return;
    showResult(data.label, data.notice, 'RESEARCH PREDICTION');
    title.focus({ preventScroll: true });
  } catch (error) {
    if (submittedRevision !== revision) return;
    const message = (error.name === 'TimeoutError' || error.name === 'AbortError') ? 'The assessment timed out. Check your connection and retry.' : error.message;
    showResult('Assessment unavailable', message || 'Please try again.', 'ACTION REQUIRED');
    modelStatus.textContent = 'Assessment failed — retry';
    title.focus({ preventScroll: true });
  } finally {
    resultPanel.setAttribute('aria-busy', 'false');
    busy = false;
    button.disabled = false;
    button.textContent = 'Assess sample ↗';
    document.querySelectorAll('.sample').forEach(sample => { sample.disabled = false; });
  }
});
