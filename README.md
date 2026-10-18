---
title: Aqua · Water Potability System
emoji: 💧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# Aqua · Water Potability System

A responsive water quality research workspace with a Flask prediction API and a reproducible scikit-learn training pipeline. The original `Water.ipynb` and `ML_Project.pdf` are retained as historical analysis.

## Run locally

Requires Python 3.11.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000. The interface works without a model and explicitly displays **Training required**. Predictions return HTTP 503 until a trained artifact is installed; example values never produce simulated predictions.

## Train a model

A trained model (`models/water.joblib`, compressed, ~8 MB) is **included** in this repository. The dataset is **not** included. To retrain, supply your original, authorized `water_potability.csv` in `data/`, with these columns:

`ph, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity, Potability`

```sh
python train.py data/water_potability.csv
```

Training writes `models/water.joblib` and `models/water.metrics.json`. The pipeline uses a deterministic, stratified 70/30 split, median imputation fitted only on training data, and a class-weighted random forest. Metrics include accuracy, balanced accuracy, a majority-class baseline, per-class precision/recall, and a confusion matrix. Review these before using the model. Restart the server after replacing the model. Train and serve with the same dependency versions; retain the training environment's exact resolved versions with your release artifact.

The included model's verified holdout metrics are recorded in `models/water.metrics.json`: accuracy 65.9%, balanced accuracy 59.1%, majority-class baseline 61.0%. The original notebook reports approximately 66% accuracy as a historical figure. No improved performance is claimed; review the confusion matrix before relying on the model, especially for the potable class.

## Deployment

```sh
# Train first if prediction functionality is required.
docker build -t aqua .
docker run --rm -p 8000:8000 aqua
```

The image includes `models/water.joblib` if trained before building. Alternatively mount a trusted model artifact and set `MODEL_PATH` to its container path. Never load a joblib file from an untrusted source: loading can execute code.

### Hugging Face Spaces (free)

The YAML block at the top of this README declares `sdk: docker` and `app_port: 8000`, so the same repository can be pushed directly to a Docker Space:

```sh
git remote add space https://huggingface.co/spaces/<your-username>/<your-space-name>
git push space main
```

Create the Space first at https://huggingface.co/new-space with the Docker SDK (or push to an existing Space). After the build finishes, verify `https://<space-url>/health` reports `"model_ready": true`. The included `models/water.joblib` stays under HF's 10 MB git limit, so Git LFS is not required, and `requirements.txt` pins the exact training/serving versions.

The container runs Gunicorn as a non-root user, binding to `PORT` (default 8000). Configure your hosting platform to build the Dockerfile, expose that port, and serve HTTPS. No credentials or external services are required. `/health` returns process health and a separate `model_ready` flag; deployments requiring prediction must check that flag. The app does not store submitted measurements.

For a non-container deployment:

```sh
gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 2 --timeout 60 app:app
```

## API

`POST /api/predict` accepts exactly nine numeric measurements as JSON, using the dataset column names above (without Potability). Validation rejects missing/extra fields, booleans, non-finite values, and values outside the application input bounds. These bounds are not safety standards. Returns `prediction` (0 or 1), `label`, and a research-use notice. Invalid input returns 400; a missing model returns 503.

## Checks

```sh
python -m unittest discover -s tests -v
```

Tests cover page/assets, prediction feature order, malformed measurements, unavailable models, request size limits, and security headers. Tests use a stub classifier; they do not establish model quality.

## Issues addressed and remaining limits

- Added the previously missing application, dependency manifest, and container deployment setup.
- Added responsive, labeled inputs, keyboard focus states, visible units, loading/error states, and an accessible result announcement.
- Fixed full-dataset imputation leakage in the new training path and made the split stratified and reproducible.
- Added strict server validation, request limits, security headers, and production serving.
- The original notebook still contains historical code with global imputation, duplicate splits, unscaled distance-based classifiers, suppressed warnings, and deprecated plotting APIs. Use `train.py` for the deployable model rather than exporting the notebook's classifier.
- Dataset provenance, independent validation, model calibration, and deployment on a hosting account remain release-owner tasks. No live deployment has been performed.

This project is for research and education. A prediction cannot certify drinking-water safety; use accredited laboratory testing and qualified guidance for real-world decisions.
