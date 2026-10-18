const form = document.querySelector('#sample-form');
const title = document.querySelector('#result-title');
const body = document.querySelector('#result-body');
const tag = document.querySelector('#result-tag');
const button = document.querySelector('#analyze');
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
document.querySelector('#example').addEventListener('click', () => {
  form.querySelectorAll('input').forEach(input => { input.value = input.dataset.example; });
  title.textContent = 'Example loaded';
  body.textContent = 'These illustrative measurements are for exploring the interface. They are not a verified laboratory sample.';
  tag.textContent = 'EXAMPLE SAMPLE';
});
form.addEventListener('reset', () => {
  title.textContent = 'Ready for a fresh sample.';
  body.textContent = 'Enter all nine measurements to begin an assessment.';
  tag.textContent = 'AWAITING SAMPLE';
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  button.disabled = true;
  button.textContent = 'Assessing…';
  try {
    const values = Object.fromEntries([...new FormData(form)].map(([key, value]) => [key, Number(value)]));
    const response = await fetch('/api/predict', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(values)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Assessment failed. Please try again.');
    title.textContent = data.label;
    body.textContent = data.notice;
    tag.textContent = 'RESEARCH PREDICTION';
  } catch (error) {
    title.textContent = 'Assessment unavailable';
    body.textContent = error.message;
    tag.textContent = 'ACTION REQUIRED';
  } finally {
    button.disabled = false;
    button.textContent = 'Assess sample ↗';
  }
});
