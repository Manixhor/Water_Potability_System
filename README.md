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

### Why accuracy plateaus near 66%

The nine measurements carry little signal. In a 5-fold cross-validated sweep of 16 random-forest configurations every result landed between 65.8% and 67.7%, and a model that always answers "not potable" already scores 61.0%. The shipped 65.9% is therefore close to what this dataset supports, not a sign that the pipeline needs more tuning or a different classifier. No accuracy above 68% is claimed or achievable here without letting information cross the train/test boundary.

Results far above that range are almost always produced by rows appearing on both sides of the split. `scratch/leaky_accuracy.py` (on the `demo/leaky-accuracy` branch — a teaching demo, not deployed and not part of the app) reproduces the ladder on the same forest, changing only the order of the preprocessing steps:

| Pipeline | Accuracy |
| --- | --- |
| Honest: split first, impute from the training rows only | 65.9% |
| Impute medians from the whole dataset, then split | 65.5% |
| Balance the classes before the split | 76.5% |
| Duplicate every row once, then split | 88.6% |
| Duplicate every row twice, then split | 97.2% |
| No holdout at all — score on the training rows | 100.0% |

Only the first row measures generalisation; the rest measure memorisation. A held-out score means something only when the held-out rows were never touched — including by imputers, scalers, and resamplers.

## Deployment

### Cloudflare Workers (free, no Docker)

A static build with browser-side inference runs entirely on Cloudflare's **free** Workers tier — always on, no server, no Docker, no container platform:

```sh
python scripts/build_cloudflare.py   # render UI, export binary forest, verify parity
npx wrangler deploy                  # first run prompts for Cloudflare login
```

The build renders the same Jinja template the Flask app uses and exports the fitted pipeline (imputer medians + 500 trees) to a compact `AQF1` binary (`dist/static/water.forest`, ~12 MB). The browser maps typed arrays directly over the downloaded buffer, so loading is instant and each prediction is a synchronous tree walk — no WASM, workers, or runtime dependencies (an ONNX Runtime Web prototype was discarded because model parsing blocked the main thread long enough for browsers to kill the tab). The build refuses to run unless the export predicts identically to the installed scikit-learn model on every dataset row (verified: 100%, with 52/52 spot checks also passing in a real browser against the Flask API). The browser front-end (`static/app.browser.js`, served as `/static/app.js`) mirrors the Flask UI's validation and result strings; `/health` is served by `cloudflare/worker.js` and security headers live in `cloudflare/_headers`. The Flask server remains the reference implementation and is unchanged.

**Live deployment:** https://waterpotabilitysystem.promptcraft-worker.workers.dev (`/health` reports `"model_ready": true`).

### Docker

```sh
# Train first if prediction functionality is required.
docker build -t aqua .
docker run --rm -p 8000:8000 aqua
```

The image includes `models/water.joblib` if trained before building. Alternatively mount a trusted model artifact and set `MODEL_PATH` to its container path. Never load a joblib file from an untrusted source: loading can execute code.

### Hugging Face Spaces note

Hugging Face now requires a paid PRO plan to create Docker Spaces (only static HTML Spaces are free). The YAML block at the top of this README (`sdk: docker`, `app_port: 8000`) is retained so the repository can be pushed to a Docker Space on a PRO account later; the model stays under HF's 10 MB git limit, so Git LFS is not required.

### Render (free)

Render's free web service plan (512 MB RAM) builds this Dockerfile directly:

1. Sign up at https://render.com with GitHub and create a **Web Service** from this repository.
2. Choose runtime **Docker** (auto-detects the Dockerfile) and instance **Free**.
3. Set the environment variable `WEB_CONCURRENCY=1` — the model needs ~235 MB per Gunicorn worker, so a single worker is required to fit the 512 MB free instance. `PORT` is injected by Render automatically.
4. Deploy, then verify `https://<service-name>.onrender.com/health` reports `"model_ready": true`.

Free instances spin down after 15 minutes without traffic; the first request after idle takes ~30-60 seconds to wake.

The container runs Gunicorn as a non-root user, binding to `PORT` (default 8000) with a worker count set by `WEB_CONCURRENCY` (default 2; use 1 on 512 MB free instances). Configure your hosting platform to build the Dockerfile, expose that port, and serve HTTPS. No credentials or external services are required. `/health` returns process health and a separate `model_ready` flag; deployments requiring prediction must check that flag. The app does not store submitted measurements.

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
- Added one-click sample presets below the form (balanced, low-solids, higher-mineral) that the served model classifies as potable, each with a **Drinkable** verdict badge and a table listing all nine measurements with units. **Load example** loads the same balanced sample, so every built-in starting point predicts drinking water. Badge labels are checked against the model at build time (the build fails on any mismatch), clicking a preset scrolls the result into view, and the research disclaimer is unchanged.
- Fixed full-dataset imputation leakage in the new training path and made the split stratified and reproducible. The README now documents the honest accuracy ceiling (65.8-67.7% across 16 forest configurations under 5-fold cross-validation, against a 61.0% majority baseline) and the `demo/leaky-accuracy` branch shows how identical preprocessing mistakes inflate the same forest to 88.6%.
- Added strict server validation, request limits, security headers, and production serving.
- The original notebook still contains historical code with global imputation, duplicate splits, unscaled distance-based classifiers, suppressed warnings, and deprecated plotting APIs. Use `train.py` for the deployable model rather than exporting the notebook's classifier.
- Dataset provenance, independent validation, and model calibration remain release-owner tasks. The application is deployed for free on Cloudflare Workers (always on, no Docker) at https://waterpotabilitysystem.promptcraft-worker.workers.dev, verified via `/health`, production header checks, and browser parity tests against the Flask API.

This project is for research and education. A prediction cannot certify drinking-water safety; use accredited laboratory testing and qualified guidance for real-world decisions.


### Interface verification

Flask and the static build share `static/app.js`. The static build additionally loads `static/forest.js`, generated from `static/app.browser.js`, to run the same trained forest locally. Model downloads time out after 30 seconds and can be retried. Editing or clearing a sample invalidates any pending result.

Build before testing the browser model:

```sh
.venv/bin/python scripts/build_cloudflare.py
.venv/bin/python -m unittest discover -s tests -v
```

The model test runs the actual JavaScript predictor against every dataset row and compares it with scikit-learn (requires Node.js). Optional UI checks use Playwright: start Flask on port 8086, then run `node tests/browser.cjs` with Playwright available. `WATER_TEST_URL` and `PLAYWRIGHT_EXECUTABLE_PATH` can override the server and browser paths. The checks cover both Flask and static assets, five viewport widths, required fields, range validation, all presets, reset during an active request, and model-download retry.


Assessment feedback now appears directly below the form. Both manual assessments and presets focus and reveal the result, with visible loading and retry states. Presets support browsers without `requestSubmit`, and model downloads use an AbortController timeout compatible with browsers lacking `AbortSignal.timeout`. Deployed asset URLs include content versions to keep the interface and model in sync. Controller regression checks cover visible feedback, legacy preset submission, retry recovery, and stale results after resetting.
