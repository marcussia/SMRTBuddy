
# Rail Corrugation Classification

## Objective

The Rail Corrugation task requires classifying each 1-second train recording into one of three classes:

- `Normal`
- `Side I`
- `Side II`

The current solution uses vibration, shock, speed, frequency, spatial sensor location, and time-frequency information to classify the rail condition.

---

## Dataset

The training dataset contains **272 labelled recordings**:

| Class | Samples |
|---|---:|
| Normal | 234 |
| Side I | 14 |
| Side II | 24 |

Each CSV contains **1 second of data sampled at 10,000 Hz**.

Each recording contains:

- Rotating-speed signal
- 64 axle-box locations
- Vibration signal for each axle box
- Shock signal for each axle box

This gives **128 vibration/shock sensor channels** per recording.

The sensor positions also correspond to the two rail sides:

- Positions 1, 3, 5, 7 → Side I
- Positions 2, 4, 6, 8 → Side II

This spatial information is important because the model must identify not only whether corrugation exists, but also which rail side is affected.

---

## Research Motivation

Rail-corrugation research suggests that axle-box vibration contains information about rail condition.

Important findings from the literature include:

1. Corrugation creates characteristic vibration frequencies.
2. Train speed affects the observed vibration frequency.
3. Time-frequency analysis can reveal defect-related vibration patterns.
4. Vibration from the two rail sides can interact, so side-to-side comparisons may be useful.
5. Models such as SVM, Random Forest, neural networks and deep-learning approaches have previously been applied to rail-corrugation detection.

These findings guided the feature engineering, but all feature/model decisions were subsequently tested on the provided LTA training data.

---

# Feature Engineering

The raw sensor signals are transformed into several groups of features.

## 1. Base Features — 89 features

Initial features describe general vibration and shock behaviour.

Examples include:

- RMS
- Standard deviation
- Peak
- Peak-to-peak
- Kurtosis
- Crest factor
- Spectral centroid
- Spectral entropy
- Broad frequency-band energy
- Speed
- Side I vs Side II differences

EDA showed that vibration magnitude contains useful information, but is also strongly affected by train speed.

Side-to-side vibration differences were particularly informative.

---

## 2. Refined Frequency Features — +138 features

Rail corrugation is periodic, so frequency-domain information was investigated.

Additional features include:

- Finer 100-Hz frequency bands
- Dominant frequency
- Dominant-frequency power
- Spectral peak concentration
- Speed-normalised frequency
- Variation in spectral behaviour across sensors
- Side I vs Side II frequency differences

Running total:

```text
89 + 138 = 227 candidate features
```

Frequency features alone did not outperform the original representation, but combining them with the existing features improved classification.

---

## 3. Spatial Features — +172 features

Initially, measurements from the 32 sensors on each side were heavily aggregated.

This potentially discarded information about **where across the train abnormal vibration occurred**.

Spatial features were therefore added, including:

- Maximum sensor vibration
- Median sensor vibration
- 75th/90th percentiles
- Sensor-to-sensor variability
- Individual car Side I vs Side II differences
- Spatial frequency-band differences

Running total:

```text
227 + 172 = 399 candidate features
```

Adding spatial information substantially improved validation performance, showing that the location and distribution of vibration across axle boxes contains useful information.

---

## 4. Time-Frequency Features — +300 features

Whole-signal FFT features describe which frequencies occur during the 1-second recording, but largely discard **when those frequencies occur**.

STFT-based time-frequency features were therefore added.

For selected frequency regions, features describe:

- Mean energy over time
- Variation in energy over time
- Maximum energy
- 90th-percentile energy
- Burst/concentration behaviour
- Variation across sensors
- Side I vs Side II differences

Final candidate representation:

```text
89 base
+ 138 refined frequency
+ 172 spatial
+ 300 time-frequency
--------------------------------
= 699 candidate features
```

---

# Feature Selection

The final classifier does **not** use all 699 features.

The dataset contains only 272 labelled recordings, so using every candidate feature would increase the risk of overfitting.

Feature selection is therefore performed **inside each training fold only**.

```text
699 candidate features
        ↓
Random Forest feature importance
(training data only)
        ↓
Top 100 features
        ↓
Final classifier
```

Different feature counts were tested:

| Selected Features | OOF Macro F1 |
|---:|---:|
| 50 | 0.7211 |
| 75 | 0.7362 |
| **100** | **0.7588** |
| 125 | 0.7478 |
| 150 | 0.7332 |
| 200 | 0.7492 |

100 features currently provide the best balance between retaining useful information and limiting noise/redundancy.

---

# Model Selection

Several classifier families were compared, including:

- Random Forest
- CatBoost
- RBF SVM
- Extra Trees

Using the improved feature representation, Random Forest performed strongest.

Random Forest was therefore retained and a small controlled hyperparameter search was performed.

Current configuration:

```text
n_estimators = 750
min_samples_leaf = 1
max_features = 0.5
class_weight = balanced
```

Model tuning produced only a small improvement compared with the improvements produced by better feature engineering.

This suggests that **representing the sensor signals appropriately was more important than increasing model complexity**.

---

# Current Pipeline

```text
Raw LTA sensor data
        ↓
Vibration + Shock + Speed
        ↓
┌─────────────────────────────────┐
│ Time-domain features            │
│ Frequency-domain features       │
│ Spatial sensor features         │
│ STFT time-frequency features    │
│ Side I vs Side II differences   │
└─────────────────────────────────┘
        ↓
699 candidate features
        ↓
Fold-safe feature selection
        ↓
Top 100 features
        ↓
Random Forest
        ↓
┌────────┬────────┬─────────┐
│ Normal │ Side I │ Side II │
└────────┴────────┴─────────┘
```

---

# Validation

Because the classes are highly imbalanced, **accuracy is not used as the main evaluation metric**.

The challenge uses **Macro F1**, which gives equal importance to:

- Normal
- Side I
- Side II

The model was evaluated using stratified 5-fold cross-validation.

Feature selection was performed separately inside each training fold to prevent validation leakage.

The final candidate pipeline was then tested using **five different cross-validation random seeds**, producing 25 validation folds in total.

## Repeated Cross-Validation Results

| Metric | Mean F1 | Std |
|---|---:|---:|
| **Macro F1** | **0.7423** | **0.0428** |
| Normal | 0.9616 | 0.0040 |
| Side I | 0.4185 | 0.1153 |
| Side II | 0.8469 | 0.0155 |

Macro F1 across the five CV seeds ranged from:

```text
0.7072 – 0.8101
```

The mean across all 25 individual validation-fold Macro F1 scores was approximately:

```text
0.7469
```

---

# Main Limitation

Side I remains the most difficult class.

There are only:

```text
14 Side I samples
```

compared with:

```text
24 Side II
234 Normal
```

Side I performance therefore varies substantially depending on which examples are present in each training fold.

Repeated validation showed:

```text
Side I mean F1 = 0.4185
Side I std     = 0.1153
```

This is currently the largest source of uncertainty in the Rail model.

---

# Feature Stability

Feature selection was repeated across 25 different training folds.

Results showed:

```text
28 features selected in 25/25 folds
40 features selected in at least 24/25 folds
61 features selected in at least 20/25 folds
80 features selected in at least 15/25 folds
```

Frequently selected feature families included:

- Side I vs Side II vibration RMS differences
- Spatial vibration magnitude
- Car-level side differences
- Shock differences
- 200–300 Hz time-frequency behaviour
- 400–500 Hz time-frequency behaviour
- Higher-frequency time-frequency behaviour

This indicates that many of the important feature families remain useful across different training/validation partitions.

---

# Current Status

Current Rail Pipeline v1:

```text
Repeated-CV Macro F1 ≈ 0.742 ± 0.043
```

The pipeline has been developed and validated using **only the 272 labelled training recordings**.

The official Test dataset has not been used for feature selection, model selection, hyperparameter tuning, or validation.

---

# Next Steps

When the Rail pipeline is finalised:

1. Extract the complete final feature representation for all 272 labelled training files.
2. Select the final top 100 features using the complete training dataset.
3. Train the final Random Forest using all 272 labelled recordings.
4. Save the selected feature list and trained model.
5. Apply the exact same feature-extraction pipeline to the official Test files.
6. Generate the required predictions:

```text
Normal
Side I
Side II
```

7. Export the predictions in the required submission format.

The hidden Test labels remain unseen; therefore the final Test Macro F1 will be determined by the challenge evaluator.