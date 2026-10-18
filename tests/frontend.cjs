// Exercise the actual UI controller without browser automation or network calls.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function environment({ visible = false, reduced = false } = {}) {
  const elements = {};
  function element(id) { return elements[id] ||= { textContent: '', hidden: true, dataset: {}, listeners: {}, disabled: false,
    addEventListener(type, fn) { this.listeners[type] = fn; }, setAttribute() {},
    focus() { this.focused = true; }, scrollIntoView(options) { this.revealed = true; this.scrolls = (this.scrolls || 0) + 1; this.scrollOptions = options; },
    getBoundingClientRect() { return visible ? {top:100,bottom:140} : {top:1000,bottom:1040}; } }; }
  const inputs = ['ph','Hardness'].map(name => ({ ...element(name), name, id: name, min: '0', max: '1000', valueAsNumber: 7, dataset: {example:'7'} }));
  const form = element('#sample-form');
  form.querySelectorAll = () => inputs;
  form.reportValidity = () => true;
  form.dispatchEvent = event => form.listeners[event.type](event);
  const sample = element('preset'); sample.dataset.sample = '{"ph":7,"Hardness":100}';
  const context = vm.createContext({ document: {
    querySelector: element, querySelectorAll: () => [sample]
  }, window: { innerHeight: 812, matchMedia: () => ({matches: reduced}), aquaModel: { ready: async () => true, predict: async () => ({label:'Predicted potable',notice:'Research only'}) } },
    Event, AbortController, setTimeout, clearTimeout });
  vm.runInContext(fs.readFileSync('static/app.js','utf8'), context);
  return {elements, form, sample, inputs, model:context.window.aquaModel};
}
async function main() {
  let e = environment();
  await e.form.listeners.submit(new Event('submit', {cancelable:true}));
  assert.equal(e.elements['#result-title'].textContent,'Predicted potable');
  assert(e.elements['.result'].revealed, 'Manual assessments must reveal the result');
  assert(e.elements['#result-title'].focused);
  assert.equal(e.elements['.result'].scrolls, 1, 'Do not scroll again when the answer arrives');
  assert.equal(e.elements['.result'].scrollOptions.behavior, 'smooth');
  e = environment({visible: true});
  await e.form.listeners.submit(new Event('submit', {cancelable:true}));
  assert.equal(e.elements['.result'].scrolls || 0, 0, 'Keep the viewport still when the result is visible');
  e = environment({reduced: true});
  await e.form.listeners.submit(new Event('submit', {cancelable:true}));
  assert.equal(e.elements['.result'].scrollOptions.behavior, 'auto');
  e = environment();
  // Legacy browsers without requestSubmit or AbortSignal.timeout must still assess presets.
  e.sample.listeners.click();
  await new Promise(resolve => setTimeout(resolve,0));
  assert.equal(e.elements['#result-title'].textContent,'Predicted potable');
  e = environment();
  e.model.predict = async () => { throw new Error('connection failed'); };
  await e.form.listeners.submit(new Event('submit',{cancelable:true}));
  assert.equal(e.elements['#result-title'].textContent,'Assessment unavailable');
  assert.equal(e.elements['#retry'].hidden,false);
  assert.equal(e.elements['#analyze'].disabled,false);
  e.model.predict = async () => ({label:'Predicted non-potable',notice:'Research only'});
  await e.elements['#retry'].listeners.click();
  await new Promise(resolve => setTimeout(resolve,0));
  assert.equal(e.elements['#result-title'].textContent,'Predicted non-potable');
  e = environment();
  let complete;
  e.model.predict = () => new Promise(resolve => { complete = resolve; });
  const pending = e.form.listeners.submit(new Event('submit',{cancelable:true}));
  assert.equal(e.elements['#result-tag'].textContent,'ASSESSING');
  e.form.listeners.reset();
  complete({label:'STALE',notice:'old sample'});
  await pending;
  assert.equal(e.elements['#result-tag'].textContent,'AWAITING SAMPLE');
  console.log('Passed: manual visibility, legacy preset submission, retry, loading and reset races.');
}
main().catch(error => { console.error(error); process.exitCode=1; });
