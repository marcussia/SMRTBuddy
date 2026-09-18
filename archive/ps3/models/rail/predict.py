
from pathlib import Path
import argparse
import json

import joblib
import pandas as pd

from feature_extraction import extract_features


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACT_DIR / "rail_model.joblib"
FEATURE_PATH = ARTIFACT_DIR / "selected_features.json"

VALID_LABELS = {
    "Normal",
    "Side I",
    "Side II"
}


# ============================================================
# LOAD FINAL MODEL
# ============================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}\n"
        "Run train.py first."
    )

if not FEATURE_PATH.exists():
    raise FileNotFoundError(
        f"Selected feature list not found: {FEATURE_PATH}\n"
        "Run train.py first."
    )


model = joblib.load(MODEL_PATH)


with open(FEATURE_PATH, "r") as file:
    selected_features = json.load(file)


if len(selected_features) != 100:
    raise ValueError(
        "Expected 100 selected features, "
        f"found {len(selected_features)}."
    )


# ============================================================
# NATURAL FILE SORTING
# Test1.csv, Test2.csv, ... Test10.csv
# instead of Test1, Test10, Test11, ...
# ============================================================

def file_number(path):

    digits = "".join(
        character
        for character in path.stem
        if character.isdigit()
    )

    if digits:
        return int(digits)

    return float("inf")


# ============================================================
# PREDICT ONE FILE
# ============================================================

def predict_file(csv_path):

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {csv_path}"
        )

    # --------------------------------------------------------
    # Exact verified 699-feature extraction
    # --------------------------------------------------------

    features = extract_features(csv_path)

    if len(features) != 699:
        raise ValueError(
            "Expected 699 extracted features, "
            f"found {len(features)}."
        )

    # --------------------------------------------------------
    # Ensure all final selected features exist
    # --------------------------------------------------------

    missing = [
        feature
        for feature in selected_features
        if feature not in features
    ]

    if missing:
        raise ValueError(
            "Missing selected features:\n"
            + "\n".join(missing)
        )

    # --------------------------------------------------------
    # Exact feature order used by final model
    # --------------------------------------------------------

    X = pd.DataFrame([
        {
            feature: features[feature]
            for feature in selected_features
        }
    ])

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    prediction = model.predict(X)[0]

    if prediction not in VALID_LABELS:
        raise ValueError(
            f"Invalid model prediction: {prediction}"
        )

    # --------------------------------------------------------
    # Probabilities
    #
    # Useful for UI / individual predictions.
    # NOT included in official submission CSV.
    # --------------------------------------------------------

    probabilities = model.predict_proba(X)[0]

    probability_dict = {
        class_name: float(probability)
        for class_name, probability
        in zip(
            model.classes_,
            probabilities
        )
    }

    return {
        "file_id": csv_path.name,
        "prediction": prediction,
        "probabilities": probability_dict
    }


# ============================================================
# PREDICT DIRECTORY
# ============================================================

def predict_directory(
    input_dir,
    output_path
):

    input_dir = Path(input_dir)
    output_path = Path(output_path)

    files = sorted(
        input_dir.glob("*.csv"),
        key=file_number
    )

    if len(files) == 0:
        raise ValueError(
            f"No CSV files found in {input_dir}"
        )

    print(
        f"\nFiles found: {len(files)}"
    )

    rows = []

    for i, path in enumerate(
        files,
        start=1
    ):

        result = predict_file(path)

        # ----------------------------------------------------
        # OFFICIAL RAIL SUBMISSION FORMAT
        #
        # Exactly:
        # file_id,prediction
        # ----------------------------------------------------

        rows.append({
            "file_id":
                result["file_id"],

            "prediction":
                result["prediction"]
        })

        print(
            f"[{i}/{len(files)}] "
            f"{path.name} -> "
            f"{result['prediction']}"
        )

    results_df = pd.DataFrame(
        rows,
        columns=[
            "file_id",
            "prediction"
        ]
    )

    # --------------------------------------------------------
    # FINAL SUBMISSION SANITY CHECKS
    # --------------------------------------------------------

    if results_df[
        "file_id"
    ].duplicated().any():

        raise ValueError(
            "Duplicate file_id values "
            "detected."
        )

    invalid_predictions = (
        set(
            results_df[
                "prediction"
            ].unique()
        )
        - VALID_LABELS
    )

    if invalid_predictions:

        raise ValueError(
            "Invalid predictions detected: "
            f"{invalid_predictions}"
        )

    results_df.to_csv(
        output_path,
        index=False
    )

    print(
        "\nPredictions saved:"
    )

    print(output_path)

    print(
        "\nPrediction counts:"
    )

    print(
        results_df[
            "prediction"
        ].value_counts()
    )

    print(
        "\nSubmission columns:"
    )

    print(
        results_df.columns.tolist()
    )

    print(
        "\nRows:",
        len(results_df)
    )

    return results_df


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Rail corrugation classification"
        )
    )

    parser.add_argument(
        "input",
        help=(
            "Path to one Rail CSV "
            "or a directory of Rail CSV files"
        )
    )

    parser.add_argument(
        "--output",
        default="rail_predictions.csv",
        help=(
            "Output CSV path when predicting "
            "a directory"
        )
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    # --------------------------------------------------------
    # ONE FILE
    # --------------------------------------------------------

    if input_path.is_file():

        result = predict_file(
            input_path
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "RAIL CORRUGATION PREDICTION"
        )

        print(
            "=" * 70
        )

        print(
            "\nFile:",
            result["file_id"]
        )

        print(
            "Prediction:",
            result["prediction"]
        )

        print(
            "\nClass probabilities:"
        )

        for (
            class_name,
            probability
        ) in sorted(
            result[
                "probabilities"
            ].items(),
            key=lambda x: x[1],
            reverse=True
        ):

            print(
                f"  {class_name:7s}: "
                f"{probability:.4f}"
            )

    # --------------------------------------------------------
    # DIRECTORY
    # --------------------------------------------------------

    elif input_path.is_dir():

        predict_directory(
            input_path,
            args.output
        )

    else:

        raise FileNotFoundError(
            f"Input does not exist: "
            f"{input_path}"
        )