
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from feature_extraction import extract_features


# ============================================================
# PATHS
# ============================================================

# Raw labelled training data
TRAIN_DIR = Path(
    "/Users/enyangchen/Documents/Github/"
    "NebulaX-Hackathon-ProblemStatement/"
    "PS3/02_Datasets/Rail_Corrugation/Train"
)

# Existing validated feature tables
CACHE_DIR = Path(
    "/Users/enyangchen/Documents/Github/"
    "LTA-hackathon/external/rail"
)

BASE_PATH = (
    CACHE_DIR
    / "rail_eda_features.csv"
)

REFINED_PATH = (
    CACHE_DIR
    / "rail_refined_frequency_features.csv"
)

SPATIAL_PATH = (
    CACHE_DIR
    / "rail_spatial_features.csv"
)

TF_PATH = (
    CACHE_DIR
    / "rail_time_frequency_features.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# Small floating-point differences are okay.
RTOL = 1e-8
ATOL = 1e-10


# ============================================================
# LOAD CACHED VALIDATED FEATURES
# ============================================================

print("=" * 80)
print("RAIL PIPELINE VERIFICATION")
print("=" * 80)

print("\nLoading validated feature tables...")


base_df = pd.read_csv(
    BASE_PATH
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


# ============================================================
# MERGE INTO THE EXACT 699-FEATURE TABLE
# ============================================================

cached = (
    base_df
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


feature_columns = [
    column
    for column in cached.columns
    if column not in [
        "filename",
        "label"
    ]
]


print(
    "Cached files:",
    len(cached)
)

print(
    "Cached candidate features:",
    len(feature_columns)
)


if len(cached) != 272:

    raise ValueError(
        "Expected 272 cached files, "
        f"found {len(cached)}."
    )


if len(feature_columns) != 699:

    raise ValueError(
        "Expected 699 cached features, "
        f"found {len(feature_columns)}."
    )


# ============================================================
# VERIFY COLUMN UNIQUENESS
# ============================================================

if len(
    set(feature_columns)
) != len(feature_columns):

    raise ValueError(
        "Duplicate feature names detected "
        "in cached representation."
    )


# ============================================================
# VERIFY EVERY TRAIN FILE
# ============================================================

print(
    "\nRe-extracting features from raw CSVs..."
)

print(
    "This may take a while because all "
    "272 files are being processed."
)


max_absolute_difference = 0.0

mismatch_count = 0

mismatched_features = {}

checked_values = 0


for i, cached_row in cached.iterrows():

    filename = cached_row[
        "filename"
    ]

    raw_path = (
        TRAIN_DIR
        / filename
    )


    if not raw_path.exists():

        raise FileNotFoundError(
            f"Raw file not found: "
            f"{raw_path}"
        )


    # ========================================================
    # NEW PRODUCTION EXTRACTOR
    # ========================================================

    new_features = (
        extract_features(
            raw_path
        )
    )


    # ========================================================
    # CHECK FEATURE NAMES
    # ========================================================

    new_names = set(
        new_features.keys()
    )

    expected_names = set(
        feature_columns
    )


    missing = (
        expected_names
        - new_names
    )

    extra = (
        new_names
        - expected_names
    )


    if missing or extra:

        print(
            "\nFEATURE NAME MISMATCH"
        )

        print(
            "File:",
            filename
        )

        if missing:

            print(
                "Missing features:"
            )

            for feature in sorted(
                missing
            ):

                print(
                    " ",
                    feature
                )


        if extra:

            print(
                "Unexpected features:"
            )

            for feature in sorted(
                extra
            ):

                print(
                    " ",
                    feature
                )


        sys.exit(1)


    # ========================================================
    # NUMERICAL COMPARISON
    # ========================================================

    for feature in feature_columns:

        expected = cached_row[
            feature
        ]

        actual = new_features[
            feature
        ]


        # Handle NaN safely
        if (
            pd.isna(expected)
            and pd.isna(actual)
        ):

            continue


        checked_values += 1


        difference = abs(
            float(expected)
            - float(actual)
        )


        max_absolute_difference = max(
            max_absolute_difference,
            difference
        )


        if not np.isclose(
            expected,
            actual,
            rtol=RTOL,
            atol=ATOL,
            equal_nan=True
        ):

            mismatch_count += 1

            mismatched_features[
                feature
            ] = (
                mismatched_features
                .get(feature, 0)
                + 1
            )


            # Print only first few mismatches
            # so Terminal doesn't explode.
            if mismatch_count <= 20:

                print(
                    "\nMismatch:"
                )

                print(
                    " File:",
                    filename
                )

                print(
                    " Feature:",
                    feature
                )

                print(
                    " Cached:",
                    expected
                )

                print(
                    " New:",
                    actual
                )

                print(
                    " Difference:",
                    difference
                )


    # ========================================================
    # PROGRESS
    # ========================================================

    processed = i + 1

    if (
        processed % 25 == 0
        or processed == len(cached)
    ):

        print(
            f"Verified "
            f"{processed}/"
            f"{len(cached)} files"
        )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)

print(
    "\nFiles checked:",
    len(cached)
)

print(
    "Features per file:",
    len(feature_columns)
)

print(
    "Numerical values checked:",
    checked_values
)

print(
    "Mismatched values:",
    mismatch_count
)

print(
    "Maximum absolute difference:",
    max_absolute_difference
)


# ============================================================
# FAILURE REPORT
# ============================================================

if mismatch_count > 0:

    print(
        "\nMost common mismatched features:"
    )

    mismatch_series = (
        pd.Series(
            mismatched_features
        )
        .sort_values(
            ascending=False
        )
    )

    print(
        mismatch_series
        .head(30)
        .to_string()
    )


    print(
        "\n❌ PIPELINE VERIFICATION FAILED"
    )

    print(
        "Do NOT train the final model yet."
    )

    sys.exit(1)


# ============================================================
# SUCCESS
# ============================================================

print(
    "\n✓ BASE FEATURES MATCH"
)

print(
    "✓ REFINED FREQUENCY FEATURES MATCH"
)

print(
    "✓ SPATIAL FEATURES MATCH"
)

print(
    "✓ TIME-FREQUENCY FEATURES MATCH"
)

print(
    "\n✓ ALL 699 FEATURES VERIFIED"
)

print(
    "\nPIPELINE VERIFICATION PASSED."
)

print(
    "\nThe production feature extractor "
    "reproduces the feature representation "
    "used during model development."
)

print(
    "\nIt is now safe to run train.py."
)