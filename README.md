# Water Potability Prediction System

A machine learning project that predicts whether water is **potable** (safe to drink) or **not potable** based on chemical water quality metrics.

## Overview

This project trains and compares multiple classification models on a water quality dataset to determine the best approach for potability prediction. The complete pipeline — from exploratory data analysis (EDA) to model evaluation — is implemented in a Jupyter Notebook.

## Dataset

The dataset contains **3276 samples** with **9 chemical features**:

| Feature | Description |
|---|---|
| pH | pH level of water |
| Hardness | Water hardness (mg/L) |
| Solids | Total dissolved solids (ppm) |
| Chloramines | Chloramine concentration (ppm) |
| Sulfate | Sulfate concentration (mg/L) |
| Conductivity | Electrical conductivity (µS/cm) |
| Organic_carbon | Organic carbon content (mg/L) |
| Trihalomethanes | Trihalomethane concentration (µg/L) |
| Turbidity | Water turbidity (NTU) |

**Target:** `Potability` — 0 (Not Potable) or 1 (Potable)

**Class Distribution:** 1998 non-potable (61%) | 1278 potable (39%)

## Models & Performance

| Model | Accuracy |
|---|---|
| Logistic Regression | 60.53% |
| K-Nearest Neighbors (k=3) | 51.98% |
| Support Vector Machine | 60.53% |
| Decision Tree | 59.72% |
| **Random Forest (500 estimators)** | **66.02%** |

The **Random Forest classifier** achieves the highest accuracy at ~66%.

## Pipeline

1. **Data Loading & EDA** — Initial exploration, statistics, missing value detection
2. **Data Cleaning** — Missing values filled with column means
3. **Visualization** — KDE plots, histograms, box plots, class distribution charts
4. **Train/Test Split** — 70/30 split using `train_test_split`
5. **Model Training** — 5 classifiers from scikit-learn
6. **Evaluation** — Accuracy scores and confusion matrices

## Tech Stack

- Python 3.11
- pandas, numpy (data manipulation)
- matplotlib, seaborn, plotly (visualization)
- scikit-learn (ML models)

## Usage

Open `Water.ipynb` in Jupyter Notebook or JupyterLab and run all cells. The notebook handles the entire workflow end-to-end.

## Project Structure

```
Water_Potability_System/
├── Water.ipynb          # Main analysis notebook
├── ML_Project.pdf       # Project report (29 pages)
└── README.md            # This file
```

## Results

The Random Forest model performs best with 66% accuracy. The dataset exhibits class imbalance, which could be addressed in future iterations with resampling techniques.
