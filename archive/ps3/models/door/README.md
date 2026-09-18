
# Door Abnormal Resistance Detection

## Objective

The Door task requires detecting individual door operation cycles from a continuous sensor stream and classifying each detected cycle as:

- `Normal`
- `Abnormal resistance`

Unlike Rail, each row in the Test data is not an independent prediction.

The Door pipeline therefore has **two stages**:

```text
Continuous door sensor stream
            ↓
1. SEGMENTATION
Detect individual door cycles
            ↓
2. CLASSIFICATION
Normal / Abnormal resistance
            ↓
start_time | end_time | prediction
```

Both parts matter because the Door task is evaluated using **IoU-weighted F1**, which considers both:

- whether the predicted segment boundaries overlap the true door cycle correctly
- whether the cycle is assigned the correct class

---

# Dataset

The training data consists of one continuous sensor stream:

```text
Train.csv
18,036 rows
```

Ground-truth segment labels identify **110 door cycles**:

| Status | Cycles |
|---|---:|
| Normal | 80 |
| Abnormal resistance | 30 |
| **Total** | **110** |

The cycles are also evenly divided between opening and closing operations:

| Operation | Normal | Abnormal | Total |
|---|---:|---:|---:|
| Open | 40 | 15 | 55 |
| Close | 40 | 15 | 55 |

Each row contains door-system measurements including:

- motor current
- motor voltage
- motor back-EMF
- door opening/closing state
- controller commands
- door switches
- door-leaf position

The provided Test stream contains:

```text
6,253 rows
```

and its reference segment boundaries and labels are hidden.

---

# 1. Segmentation

Before classifying a door condition, the continuous stream must first be separated into individual door cycles.

EDA showed that samples inside a door cycle are normally recorded every:

```text
0.02 seconds
```

However, there are large timestamp gaps between consecutive door operations.

A simple segmentation rule was therefore tested:

```text
If timestamp gap > 1 second
        ↓
start a new door cycle
```

On the complete training stream this produced:

```text
True cycles detected:     110 / 110

Exact start times:        110 / 110
Exact end times:          110 / 110
Exact row counts:         110 / 110
```

Therefore, a machine-learning model is not required for segmentation.

The same timestamp structure also exists in the provided Test stream:

```text
37 large timestamp gaps
        ↓
38 detected Test cycles
```

The production pipeline therefore uses deterministic timestamp-gap segmentation.

---

# 2. Understanding Abnormal Resistance

Initial EDA investigated whether simple properties such as door-cycle duration could identify abnormal resistance.

Opening and closing have very consistent but different durations:

```text
Open  ≈ 2.82 seconds
Close ≈ 3.70 seconds
```

However, within the same operation, Normal and Abnormal cycles have very similar durations.

Therefore:

```text
longer cycle ≠ automatically abnormal
```

The main difference instead appears in **motor behaviour while the door is moving**.

Abnormal resistance generally causes the motor to work harder during particular parts of the door movement.

---

# Research Motivation

Research into train-door systems and DC motors helped explain the patterns observed during EDA and guided additional feature engineering.

## Motor Current and Mechanical Load

For a DC motor, motor torque is related to motor current.

Conceptually:

```text
More mechanical resistance
        ↓
Greater motor load
        ↓
More torque required
        ↓
Higher motor current
```

This matches the provided Door data: abnormal cycles generally show increased motor current during the affected portions of door movement.

This motivated features based on:

- average and RMS current
- integrated current
- current relative to door movement
- electrical power proxies

## Resistance Can Be Localised

Train-door research also reports that abnormal resistance can occur during specific stages of opening or closing rather than affecting the entire operation equally.

Our EDA found the same behaviour.

For **Open** cycles, the strongest abnormal-current differences generally occur around the early/middle part of the movement.

For example:

```text
Cycle progress       Abnormal vs Normal current

0–10%                     +4%
10–20%                   +40%
20–30%                  +144%
30–40%                  +111%
40–50%                   +88%
50–60%                  +103%
```

For **Close** cycles, the strongest differences occur mainly through the middle/later movement:

```text
30–40%                   +53%
40–50%                  +206%
50–60%                  +421%
60–70%                 very large difference
70–80%                   +48%
80–90%                   +81%
```

This motivated **phase-specific features** rather than describing an entire cycle using only one average value.

## Wavelet Features

Research also suggests that wavelet analysis can identify localised changes in motor-current signals caused by abnormal mechanical load.

Wavelet features were therefore tested on the Door data rather than included automatically.

The experiments showed:

```text
Full representation with wavelets:
F1 = 1.000

Removing wavelets:
F1 ≈ 0.983
```

The same difference appeared during temporal validation.

Wavelet information therefore appears to help classify one of the more difficult abnormal cycles and was retained in Door v1.

---

# Feature Engineering

Each detected door cycle is converted into a compact **27-feature representation**.

The features describe several aspects of the physical door system.

## Motor Current

Examples:

```text
mean absolute current
current RMS
integrated current
current relative to door movement
```

These describe how much electrical effort the motor uses during the operation.

## Voltage and Back-EMF

Voltage and motor back-EMF provide additional information about the electrical and motion state of the motor.

## Door Movement

Door-leaf position is used to describe:

- movement speed
- periods of little movement
- motor effort relative to movement

A particularly useful idea is:

```text
motor current
─────────────
door movement
```

which approximates how much motor effort is required to produce movement.

## Phase-Specific Features

Each cycle is normalised and divided into movement phases.

Current and electrical-power behaviour are measured separately within these phases.

This preserves the fact that abnormal resistance may occur only during a particular part of door travel.

## Current-Change Features

Changes in motor current are measured to capture sudden changes in motor load.

## Wavelet Features

Discrete wavelet features describe localised changes in the current signal that may be hidden by whole-cycle averages.

---

# Classification Model

Several model types were initially compared, including:

- Logistic Regression
- Random Forest
- Gradient Boosting
- RBF SVM

The final candidate is a compact **RBF Support Vector Machine (SVM)**.

Pipeline:

```text
Detected door cycle
        ↓
27 engineered features
        ↓
StandardScaler
        ↓
RBF SVM
        ↓
Normal / Abnormal resistance
```

Current SVM configuration:

```text
kernel       = rbf
C            = 1.0
gamma        = scale
class_weight = balanced
```

The model is deliberately small because only 110 labelled cycles are available.

---

# Validation

Because the training dataset is small, a single train/validation split would provide an unstable estimate of performance.

The model was therefore tested using several validation strategies.

## Repeated Stratified Cross-Validation

Five different shuffled 5-fold cross-validation splits were tested:

```text
Seeds:
42
7
21
100
2026
```

For the final 27-feature RBF SVM:

```text
Seed 42      F1 = 1.000
Seed 7       F1 = 1.000
Seed 21      F1 = 1.000
Seed 100     F1 = 1.000
Seed 2026    F1 = 1.000
```

Across all of these out-of-fold predictions:

```text
Normal:
80 / 80 correctly classified

Abnormal resistance:
30 / 30 correctly classified
```

---

# Temporal Robustness

Random cross-validation alone could potentially give misleading results if abnormal cycles were associated with a particular part of the continuous recording.

The model was therefore also tested using temporal holdouts:

```text
Train early cycles → validate late cycles
Train late cycles  → validate early cycles
Train outer cycles → validate middle cycles
Train middle       → validate outer cycles
```

The final 27-feature RBF SVM achieved:

```text
F1 = 1.000
```

on all four temporal validation tests.

This provides additional evidence that the classifier is learning differences in door behaviour rather than simply learning where abnormalities occur in the recording.

---

# Model Robustness

The perfect validation result was treated cautiously because the dataset contains only 110 cycles.

The SVM was therefore stress-tested using:

```text
5 different C values
×
5 different gamma values
=
25 SVM configurations
```

Of these:

```text
20 / 25 configurations
```

achieved perfect F1 across all five cross-validation seeds.

This is important because it shows that the result does not depend on one narrowly tuned SVM configuration.

---

# Feature Robustness

Different feature families were also removed to determine whether the result depended on one specific representation.

| Feature Set | Features | Mean OOF F1 |
|---|---:|---:|
| Full representation | 27 | **1.000** |
| Remove current-change features | 25 | **1.000** |
| Remove EMF/movement features | 21 | **1.000** |
| Remove wavelets | 25 | 0.983 |
| Core physical features | 16 | 0.983 |

This indicates that the Normal/Abnormal distinction is strong across several physically meaningful feature families.

Wavelet information appears to provide useful additional information for the hardest abnormal example.

---

# End-to-End Validation

The final experiment tested the **entire pipeline directly from the raw continuous training stream**.

Importantly, this did not rely on cached EDA feature tables.

```text
Raw Train.csv
18,036 rows
        ↓
Timestamp-gap segmentation
        ↓
110 detected cycles
        ↓
Production-style feature extraction
        ↓
27 features per cycle
        ↓
Cross-validated RBF SVM
        ↓
Normal / Abnormal resistance
        ↓
Predicted start/end + class
        ↓
IoU-weighted F1
```

Results:

```text
Segmentation:
110 / 110 cycles detected

Exact starts:
110 / 110

Exact ends:
110 / 110

Classification:
110 / 110 correct
```

Across all five cross-validation seeds:

```text
Classification F1:
Mean = 1.000
Min  = 1.000
Max  = 1.000

IoU-weighted F1:
Mean = 1.000
Min  = 1.000
Max  = 1.000
```

---

# What Does IoU-Weighted F1 Mean?

This is the important competition metric for Door.

A prediction must get **both the segment timing and the class correct**.

## IoU — Intersection over Union

Suppose the real door cycle is:

```text
TRUE
|------------------------|

PREDICTED
    |------------------------|
```

The prediction overlaps most of the true cycle but its timing is not exact.

IoU measures:

```text
            overlapping duration
IoU = --------------------------------
       total duration covered by either
```

Therefore:

```text
Perfect boundaries       → IoU = 1.0
Partial overlap           → IoU < 1.0
No overlap                → IoU = 0.0
```

A predicted segment also needs the **correct Normal/Abnormal label** to match the true segment.

The competition then uses these overlaps to calculate soft precision and recall, which are combined into an IoU-weighted F1 score.

So a score of:

```text
IoU-weighted F1 = 1.000
```

on our training validation means that the out-of-fold pipeline:

1. detected every door cycle,
2. produced the exact segment boundaries,
3. assigned every cycle the correct Normal/Abnormal label.

It does **not** mean that hidden Test performance is guaranteed to be 1.000.

The correct interpretation is:

> **Door v1 achieved 1.000 IoU-weighted F1 under repeated internal validation on the provided labelled training data.**

The hidden Test labels remain unseen and will determine the actual challenge score.

---

# Current Door v1 Pipeline

```text
CONTINUOUS SENSOR STREAM
          ↓
Timestamp gap > 1 second
          ↓
┌─────────────────────┐
│ Individual cycles   │
└──────────┬──────────┘
           ↓
27 FEATURES
│
├── Motor current
├── Voltage
├── Back-EMF
├── Door movement
├── Current / movement
├── Electrical power
├── Phase-specific behaviour
├── Current changes
└── Wavelet behaviour
           ↓
StandardScaler
           ↓
RBF SVM
           ↓
Normal / Abnormal resistance
           ↓
start_time | end_time | prediction
```

---

# Current Status

Door model development and internal validation are complete.

Current validated result:

```text
Repeated internal classification F1 = 1.000
Repeated end-to-end IoU-weighted F1 = 1.000
```

This result has survived:

```text
✓ multiple random CV splits
✓ temporal holdout validation
✓ SVM parameter sensitivity testing
✓ feature-family ablation
✓ raw end-to-end pipeline testing
✓ exact segmentation verification
```

Because performance on the available labelled data is already saturated, further model tuning is currently more likely to overfit the small training dataset than provide useful evidence of improvement.

---

# Next Steps

The next steps are productionisation rather than additional model experimentation:

```text
1. Create final feature_extraction.py
        ↓
2. Verify production features reproduce
   the validated pipeline
        ↓
3. Train final SVM using all 110
   labelled cycles
        ↓
4. Save final model/scaler
        ↓
5. Run the frozen pipeline on Test.csv
        ↓
6. Detect the 38 Test cycles
        ↓
7. Generate door_predictions.csv
```

The hidden Test labels will not be used during this process.

Door v1 can therefore be frozen after production verification and Test prediction generation, allowing development to move to the remaining PS3 subsystems.