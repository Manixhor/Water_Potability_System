"""Train with a stratified holdout and training-only imputation."""
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from features import FEATURES


def train(csv_path, output):
    data = pd.read_csv(csv_path)
    required = [*FEATURES, 'Potability']
    missing = set(required) - set(data.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    data = data[required].apply(pd.to_numeric, errors='raise')
    if data['Potability'].isna().any() or set(data.Potability.unique()) != {0, 1}:
        raise ValueError('Potability must contain both classes, 0 and 1, without missing labels.')
    if data[list(FEATURES)].isna().all().any():
        raise ValueError('Each feature needs at least one observed value.')
    for key, (_, _, low, high, _) in FEATURES.items():
        if not data[key].dropna().between(low, high).all():
            raise ValueError(f'{key} contains measurements outside the supported input bounds.')
    x_train, x_test, y_train, y_test = train_test_split(data[list(FEATURES)], data.Potability, test_size=.3, stratify=data.Potability, random_state=42)
    model = make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), RandomForestClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1))
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    metrics = dict(accuracy=accuracy_score(y_test, predicted), balanced_accuracy=balanced_accuracy_score(y_test, predicted), majority_baseline=float(y_test.value_counts(normalize=True).max()), confusion_matrix=confusion_matrix(y_test, predicted).tolist(), classification_report=classification_report(y_test, predicted, output_dict=True, zero_division=0), train_samples=len(x_train), test_samples=len(x_test), random_state=42)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output, compress=3)
    output.with_suffix('.metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', help='Path to the original water_potability.csv')
    parser.add_argument('--output', default='models/water.joblib')
    args = parser.parse_args()
    train(args.csv, args.output)
