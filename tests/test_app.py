import unittest
from app import create_app
from features import FEATURES


class FakeModel:
    def predict(self, frame):
        assert list(frame.columns) == list(FEATURES)
        return [1]


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(FakeModel()).test_client()
        self.sample = {key: value[4] for key, value in FEATURES.items()}

    def test_page_and_assets(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Know your water', response.data)
        self.assertIn(b'data-sample', response.data)
        self.assertIn(b'SAMPLE VALUES', response.data)
        self.assertIn(b'Not drinkable', response.data)
        self.assertIn(b'class="verdict ok"', response.data)
        self.assertIn(b'class="sample-values"', response.data)
        self.assertIn(b'22000.00', response.data)
        for asset in ('style.css', 'app.js'):
            with self.client.get('/static/' + asset) as asset_response:
                self.assertEqual(asset_response.status_code, 200)
        self.assertIn('Content-Security-Policy', response.headers)

    def test_sample_presets_match_feature_contract(self):
        from features import SAMPLES
        self.assertTrue(SAMPLES)
        for sample in SAMPLES:
            self.assertTrue(sample['name'] and sample['note'])
            self.assertIsInstance(sample['drinkable'], bool)
            self.assertEqual(set(sample['measurements']), set(FEATURES))
            for key, (_, _, low, high, _) in FEATURES.items():
                self.assertLessEqual(low, sample['measurements'][key])
                self.assertLessEqual(sample['measurements'][key], high)

    def test_prediction_and_order(self):
        response = self.client.post('/api/predict', json=self.sample)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['prediction'], 1)

    def test_invalid_values(self):
        for value in (-1, 15, True, '7', None, float('nan'), float('inf')):
            self.assertEqual(self.client.post('/api/predict', json={**self.sample, 'ph': value}).status_code, 400)
        self.assertEqual(self.client.post('/api/predict', json={}).status_code, 400)
        self.assertEqual(self.client.post('/api/predict', json={**self.sample, 'extra': 1}).status_code, 400)

    def test_missing_model(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'MODEL_PATH': '/tmp/nonexistent-water-model.joblib'}):
            client = create_app().test_client()
        self.assertFalse(client.get('/health').json['model_ready'])
        self.assertEqual(client.post('/api/predict', json=self.sample).status_code, 503)

    def test_body_limit(self):
        self.assertEqual(self.client.post('/api/predict', data='x'*20000, content_type='application/json').status_code, 413)


if __name__ == '__main__':
    unittest.main()
