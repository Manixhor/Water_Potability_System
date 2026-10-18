"""Water quality research application. Load only locally trusted model artifacts."""
import math
import os
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from features import FEATURES


def create_app(model=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
    model_path = Path(os.environ.get('MODEL_PATH', 'models/water.joblib'))
    if model is None and model_path.is_file():
        model = joblib.load(model_path)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/')
    def index():
        return render_template('index.html', features=FEATURES)

    @app.get('/health')
    def health():
        return jsonify(status='ok', model_ready=model is not None)

    @app.post('/api/predict')
    def predict():
        values = request.get_json(silent=True)
        if not isinstance(values, dict) or set(values) != set(FEATURES):
            return jsonify(error='Provide exactly the nine required measurements.'), 400
        for key, (_, _, low, high, _) in FEATURES.items():
            value = values[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                return jsonify(error=f'{FEATURES[key][0]} must be a finite number between {low} and {high}.'), 400
        if model is None:
            return jsonify(error='No trained model is installed. Complete model training before running an assessment.'), 503
        frame = pd.DataFrame([values], columns=list(FEATURES))
        prediction = int(model.predict(frame)[0])
        return jsonify(prediction=prediction, label='Predicted potable' if prediction else 'Predicted non-potable', notice='Research prediction only. This result does not certify that water is safe to drink.')

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        return error

    return app


app = create_app()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 8000)))
