"""Compare the actual JavaScript predictor with scikit-learn over the dataset."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

import joblib
import pandas as pd

from features import FEATURES

ROOT = Path(__file__).resolve().parents[1]


class BrowserModelTests(unittest.TestCase):
    def test_assessment_controller_regressions(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js is needed for the UI controller regression checks.')
        subprocess.run([node, 'tests/frontend.cjs'], cwd=ROOT, check=True, capture_output=True)

    def test_javascript_predictions_match_sklearn(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js is needed to execute the browser predictor.')
        data = pd.read_csv(ROOT / 'data' / 'water_potability.csv')[list(FEATURES)]
        # AQF1 models impute missing values; JavaScript receives NaN for JSON null.
        cases = json.loads(data.to_json(orient='values'))
        script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const context = vm.createContext({ window: {}, AbortSignal });
vm.runInContext(fs.readFileSync('static/app.browser.js', 'utf8'), context);
const bytes = fs.readFileSync('dist/static/water.forest');
context.bytes = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
context.cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const predictions = vm.runInContext(`
  const forest = parseForest(bytes);
  cases.map(row => forestPredict(forest, row.map(value => value === null ? NaN : value)));
`, context);
process.stdout.write(JSON.stringify(predictions));
'''
        result = subprocess.run([node, '-e', script], input=json.dumps(cases),
                                text=True, capture_output=True, cwd=ROOT, check=True)
        actual = json.loads(result.stdout)
        expected = joblib.load(ROOT / 'models' / 'water.joblib').predict(data).tolist()
        self.assertEqual(actual, expected)
