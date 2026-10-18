# Scratch: how a "87% accurate" model is manufactured

Not part of the app. Nothing here is deployed, and `main` still ships the honest
model (accuracy **0.659** on a 30% stratified holdout, majority baseline
**0.610**).

Run it:

```bash
python scratch/leaky_accuracy.py            # uses data/water_potability.csv
python scratch/leaky_accuracy.py /path/to/water_potability.csv
```

## What it shows

The same 500-tree forest, evaluated six ways. Only the *order of preprocessing
steps* changes between rows:

| Pipeline | Accuracy |
|---|---|
| honest: split first, impute from the training rows only | 0.659 |
| impute medians from the whole dataset, then split | 0.655 |
| balance the classes before the split | 0.765 |
| **duplicate every row once, then split** | **0.886** ← "the 87%" |
| duplicate every row twice, then split | 0.972 |
| no holdout at all — score on the training rows | 1.000 |

## Why the number climbs

Rows that appear in both the training and the test set are scored from memory,
not from generalisation. Duplicating or upsampling the data *before*
`train_test_split` puts the same rows on both sides, which is why the score
climbs towards 1.0 as the duplication grows. It is the same mistake whether the
duplicates come from `pd.concat`, a pre-split SMOTE call, or simply forgetting
to hold out data.

## What that means

None of these variants knows any more about water quality than the honest one.
The dataset's nine features carry so little signal that the honest ceiling is
around 0.68 (a sweep of 16 forest configurations with 5-fold cross-validation
lands between 0.658 and 0.677), and always predicting "not potable" already
scores 0.610.

If a tutorial or repo reports 85%+ on this dataset, the usual cause is one of
the rows above. A holdout score only means something when the held-out rows were
never touched — including by imputers, scalers, and resamplers.
