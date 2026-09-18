
from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier


# ============================================================
# SETTINGS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

ARTIFACT_DIR = (
    BASE_DIR
    / "artifacts"
)

ARTIFACT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

FEATURE_DIR = Path(
    "/Users/enyangchen/Documents/Github/"
    "LTA-hackathon/external/rail"
)

OLD_PATH = (
    FEATURE_DIR
    / "rail_eda_features.csv"
)

REFINED_PATH = (
    FEATURE_DIR
    / "rail_refined_frequency_features.csv"
)

SPATIAL_PATH = (
    FEATURE_DIR
    / "rail_spatial_features.csv"
)

TF_PATH = (
    FEATURE_DIR
    / "rail_time_frequency_features.csv"
)

N_SELECTED_FEATURES = 100
RANDOM_STATE = 42


# ============================================================
# LOAD VALIDATED FEATURE TABLES
# ============================================================

old_df = pd.read_csv(
    OLD_PATH
)

refined_df = pd.read_csv(
    REFINED_PATH
)

spatial_df = pd.read_csv(
    SPATIAL_PATH
)

tf_df = pd.read_csv(
    TF_PATH
)


df = (
    old_df
    .merge(
        refined_df,
        on="filename",
        how="inner"
    )
    .merge(
        spatial_df,
        on="filename",
        how="inner"
    )
    .merge(
        tf_df,
        on="filename",
        how="inner"
    )
)


X = df.drop(
    columns=[
        "filename",
        "label"
    ]
)

y = df[
    "label"
]


# ============================================================
# SANITY CHECKS
# ============================================================

print("=" * 80)
print("FINAL RAIL MODEL TRAINING")
print("=" * 80)

print(
    "\nTraining samples:",
    len(df)
)

print(
    "Candidate features:",
    X.shape[1]
)

print(
    "\nClass counts:"
)

print(
    y.value_counts()
)


if len(df) != 272:

    raise ValueError(
        "Expected 272 training "
        f"samples, found {len(df)}."
    )


if X.shape[1] != 699:

    raise ValueError(
        "Expected 699 candidate "
        f"features, found "
        f"{X.shape[1]}."
    )


# ============================================================
# FINAL FEATURE SELECTION
# ============================================================
#
# CV is finished.
#
# We now fit the selector using ALL 272 labelled files.

print(
    "\nSelecting final top "
    f"{N_SELECTED_FEATURES} features..."
)


selector = (
    RandomForestClassifier(
        n_estimators=500,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
)


selector.fit(
    X,
    y
)


importance = pd.Series(
    selector.feature_importances_,
    index=X.columns
)


selected_features = (
    importance
    .sort_values(
        ascending=False
    )
    .head(
        N_SELECTED_FEATURES
    )
    .index
    .tolist()
)


print(
    "Selected features:",
    len(selected_features)
)


# ============================================================
# FINAL MODEL
# ============================================================

print(
    "\nTraining final "
    "Random Forest..."
)


model = (
    RandomForestClassifier(
        n_estimators=750,
        min_samples_leaf=1,
        max_features=0.5,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
)


model.fit(
    X[
        selected_features
    ],
    y
)


# ============================================================
# SAVE MODEL
# ============================================================

MODEL_PATH = (
    ARTIFACT_DIR
    / "rail_model.joblib"
)


joblib.dump(
    model,
    MODEL_PATH
)


# ============================================================
# SAVE SELECTED FEATURES
# ============================================================

FEATURE_PATH = (
    ARTIFACT_DIR
    / "selected_features.json"
)


with open(
    FEATURE_PATH,
    "w"
) as file:

    json.dump(
        selected_features,
        file,
        indent=2
    )


# ============================================================
# SAVE FEATURE IMPORTANCE
# ============================================================

# ------------------------------------------------------------
# A. Selector importance across all 699 candidate features
# ------------------------------------------------------------

selector_importance_df = pd.DataFrame({
    "feature": importance.index,
    "selector_importance": importance.values
})

selector_importance_df = (
    selector_importance_df
    .sort_values(
        "selector_importance",
        ascending=False
    )
)

selector_importance_df.to_csv(
    ARTIFACT_DIR
    / "selector_feature_importance.csv",
    index=False
)


# ------------------------------------------------------------
# B. Final model importance across selected 100 features
# ------------------------------------------------------------

model_importance_df = pd.DataFrame({
    "feature": selected_features,
    "model_importance": model.feature_importances_
})

model_importance_df = (
    model_importance_df
    .sort_values(
        "model_importance",
        ascending=False
    )
)

model_importance_df.to_csv(
    ARTIFACT_DIR
    / "final_model_feature_importance.csv",
    index=False
)


print("\nTop 20 final model features:")

print(
    model_importance_df
    .head(20)
    .round(6)
    .to_string(index=False)
)

# ============================================================
# SAVE METADATA
# ============================================================

metadata = {

    "training_samples":
        len(df),

    "candidate_features":
        X.shape[1],

    "selected_features":
        len(selected_features),

    "model":
        "RandomForestClassifier",

    "n_estimators":
        750,

    "min_samples_leaf":
        1,

    "max_features":
        0.5,

    "class_weight":
        "balanced",

    "random_state":
        RANDOM_STATE,

    "validated_macro_f1_mean":
        0.7423,

    "validated_macro_f1_std":
        0.0428,

    "validation_method":
        (
            "Repeated stratified "
            "5-fold CV across 5 seeds"
        )
}


with open(
    ARTIFACT_DIR
    / "metadata.json",
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=2
    )


print("\n" + "=" * 80)
print("TRAINING COMPLETE")
print("=" * 80)

print(
    "\nModel saved:"
)

print(
    MODEL_PATH
)

print(
    "\nSelected features saved:"
)

print(
    FEATURE_PATH
)

print(
    "\nValidated performance "
    "(from Experiment #13):"
)

print(
    "Macro F1 = "
    "0.7423 +/- 0.0428"
)