
import re

import numpy as np
import pandas as pd

from scipy.signal import stft
from scipy.stats import kurtosis


# ============================================================
# CONSTANTS
# ============================================================

SAMPLING_RATE = 10_000

WHEEL_DIAMETER = 0.85
TEETH = 90

SIDE_I_POSITIONS = {1, 3, 5, 7}
SIDE_II_POSITIONS = {2, 4, 6, 8}

REFINED_BAND_EDGES = np.arange(
    100,
    2100,
    100
)

TF_BANDS = {
    "200_300": (200, 300),
    "400_500": (400, 500),
    "600_700": (600, 700),
    "1600_1700": (1600, 1700),
    "1800_1900": (1800, 1900),
}


# ============================================================
# SENSOR PARSING
# ============================================================

def parse_sensor_column(column):

    pattern = (
        r"(Vibration|Shock) of bearing "
        r"in position (\d+) of car (\d+)"
    )

    match = re.match(
        pattern,
        column
    )

    if match is None:
        return None

    signal_type = match.group(1)
    position = int(match.group(2))
    car = int(match.group(3))

    side = (
        "I"
        if position in SIDE_I_POSITIONS
        else "II"
    )

    return {
        "type": signal_type,
        "position": position,
        "car": car,
        "side": side,
    }


def get_sensor_groups(df):

    groups = {
        ("Vibration", "I"): [],
        ("Vibration", "II"): [],
        ("Shock", "I"): [],
        ("Shock", "II"): [],
    }

    for column in df.columns:

        info = parse_sensor_column(
            column
        )

        if info is None:
            continue

        groups[
            (
                info["type"],
                info["side"],
            )
        ].append(column)

    return groups


# ============================================================
# SPEED
# ============================================================

def estimate_speed_kmh(pulse):

    pulse = np.asarray(
        pulse
    )

    transitions = np.sum(
        pulse[1:] != pulse[:-1]
    )

    rotations = (
        transitions
        / (2 * TEETH)
    )

    duration_seconds = (
        len(pulse)
        / SAMPLING_RATE
    )

    rotations_per_second = (
        rotations
        / duration_seconds
    )

    wheel_circumference = (
        np.pi
        * WHEEL_DIAMETER
    )

    speed_mps = (
        rotations_per_second
        * wheel_circumference
    )

    return speed_mps * 3.6


# ============================================================
# BASE FEATURES
# ============================================================

def time_features(signal):

    signal = np.asarray(
        signal,
        dtype=float
    )

    rms = np.sqrt(
        np.mean(signal ** 2)
    )

    std = np.std(signal)

    peak = np.max(
        np.abs(signal)
    )

    peak_to_peak = np.ptp(
        signal
    )

    k = kurtosis(
        signal,
        fisher=True,
        bias=False
    )

    if rms > 0:
        crest_factor = peak / rms
    else:
        crest_factor = 0

    return {
        "rms": rms,
        "std": std,
        "peak": peak,
        "peak_to_peak": peak_to_peak,
        "kurtosis": k,
        "crest_factor": crest_factor,
    }


def frequency_features(signal):

    signal = np.asarray(
        signal,
        dtype=float
    )

    signal = (
        signal
        - np.mean(signal)
    )

    fft_values = np.fft.rfft(
        signal
    )

    frequencies = np.fft.rfftfreq(
        len(signal),
        d=1 / SAMPLING_RATE
    )

    power = (
        np.abs(fft_values) ** 2
    )

    if len(power) > 1:

        dominant_index = (
            np.argmax(power[1:])
            + 1
        )

        dominant_frequency = (
            frequencies[
                dominant_index
            ]
        )

    else:
        dominant_frequency = 0

    total_power = np.sum(
        power
    )

    if total_power > 0:

        spectral_centroid = (
            np.sum(
                frequencies
                * power
            )
            / total_power
        )

        probabilities = (
            power
            / total_power
        )

        probabilities = (
            probabilities[
                probabilities > 0
            ]
        )

        spectral_entropy = (
            -np.sum(
                probabilities
                * np.log(
                    probabilities
                )
            )
        )

    else:

        spectral_centroid = 0
        spectral_entropy = 0

    bands = {
        "0_100": (0, 100),
        "100_300": (100, 300),
        "300_600": (300, 600),
        "600_1000": (600, 1000),
        "1000_2000": (1000, 2000),
        "2000_5000": (2000, 5000),
    }

    band_features = {}

    for name, (
        low,
        high
    ) in bands.items():

        mask = (
            (frequencies >= low)
            & (frequencies < high)
        )

        band_power = np.sum(
            power[mask]
        )

        if total_power > 0:
            relative_power = (
                band_power
                / total_power
            )
        else:
            relative_power = 0

        band_features[
            f"band_{name}"
        ] = relative_power

    return {
        "dominant_frequency":
            dominant_frequency,

        "spectral_centroid":
            spectral_centroid,

        "spectral_entropy":
            spectral_entropy,

        **band_features,
    }


def extract_group_features(
    df,
    columns
):

    rows = []

    for column in columns:

        signal = df[
            column
        ].to_numpy()

        features = {
            **time_features(
                signal
            ),
            **frequency_features(
                signal
            ),
        }

        rows.append(
            features
        )

    return (
        pd.DataFrame(rows)
        .mean()
        .to_dict()
    )


def extract_base_features(
    df
):

    groups = get_sensor_groups(
        df
    )

    row = {}

    row["speed_kmh"] = (
        estimate_speed_kmh(
            df[
                "Rotating speed"
            ]
        )
    )

    for signal_type in [
        "Vibration",
        "Shock"
    ]:

        for side in [
            "I",
            "II"
        ]:

            columns = groups[
                (
                    signal_type,
                    side
                )
            ]

            features = (
                extract_group_features(
                    df,
                    columns
                )
            )

            prefix = (
                f"{signal_type.lower()}"
                f"_side_{side}"
            )

            for (
                feature_name,
                value
            ) in features.items():

                row[
                    f"{prefix}_"
                    f"{feature_name}"
                ] = value

    comparison_features = [
        "rms",
        "std",
        "peak",
        "peak_to_peak",
        "kurtosis",
        "crest_factor",
        "spectral_centroid",
        "spectral_entropy",
        "band_0_100",
        "band_100_300",
        "band_300_600",
        "band_600_1000",
        "band_1000_2000",
        "band_2000_5000",
    ]

    for signal_type in [
        "vibration",
        "shock"
    ]:

        for feature in (
            comparison_features
        ):

            side_i = row[
                f"{signal_type}"
                f"_side_I_{feature}"
            ]

            side_ii = row[
                f"{signal_type}"
                f"_side_II_{feature}"
            ]

            row[
                f"{signal_type}"
                f"_difference_{feature}"
            ] = (
                side_i
                - side_ii
            )

    return row


# ============================================================
# REFINED FREQUENCY FEATURES
# ============================================================

def refined_spectral_features(
    signal,
    speed_kmh
):

    signal = np.asarray(
        signal,
        dtype=float
    )

    signal = (
        signal
        - np.mean(signal)
    )

    window = np.hanning(
        len(signal)
    )

    fft_values = np.fft.rfft(
        signal * window
    )

    frequencies = np.fft.rfftfreq(
        len(signal),
        d=1 / SAMPLING_RATE
    )

    power = (
        np.abs(fft_values) ** 2
    )

    total_power = np.sum(
        power
    )

    if total_power <= 0:
        total_power = 1e-12

    features = {}

    for low in (
        REFINED_BAND_EDGES[:-1]
    ):

        high = low + 100

        mask = (
            (frequencies >= low)
            & (frequencies < high)
        )

        band_power = np.sum(
            power[mask]
        )

        features[
            f"fine_band_"
            f"{low}_{high}"
        ] = (
            band_power
            / total_power
        )

    useful_mask = (
        (frequencies >= 100)
        & (frequencies <= 2000)
    )

    useful_freq = (
        frequencies[
            useful_mask
        ]
    )

    useful_power = (
        power[
            useful_mask
        ]
    )

    if len(
        useful_power
    ) > 0:

        peak_index = np.argmax(
            useful_power
        )

        dominant_frequency = (
            useful_freq[
                peak_index
            ]
        )

        dominant_power_ratio = (
            useful_power[
                peak_index
            ]
            / total_power
        )

    else:

        dominant_frequency = 0
        dominant_power_ratio = 0

    features[
        "refined_dominant_frequency"
    ] = dominant_frequency

    features[
        "dominant_power_ratio"
    ] = dominant_power_ratio

    peak_band = (
        (
            frequencies
            >= dominant_frequency - 25
        )
        &
        (
            frequencies
            <= dominant_frequency + 25
        )
    )

    features[
        "peak_concentration"
    ] = (
        np.sum(
            power[
                peak_band
            ]
        )
        / total_power
    )

    speed_mps = (
        speed_kmh
        / 3.6
    )

    if speed_mps > 0:

        features[
            "dominant_frequency_per_speed"
        ] = (
            dominant_frequency
            / speed_mps
        )

    else:

        features[
            "dominant_frequency_per_speed"
        ] = 0

    return features


def aggregate_refined_side(
    df,
    columns,
    speed_kmh
):

    rows = []

    for column in columns:

        rows.append(
            refined_spectral_features(
                df[
                    column
                ].to_numpy(),
                speed_kmh
            )
        )

    temp = pd.DataFrame(
        rows
    )

    means = temp.mean()
    stds = temp.std()

    output = {}

    for (
        feature,
        value
    ) in means.items():

        output[
            f"{feature}_mean"
        ] = value

    for (
        feature,
        value
    ) in stds.items():

        output[
            f"{feature}_sensor_std"
        ] = value

    return output


def extract_refined_features(
    df,
    speed_kmh
):

    groups = get_sensor_groups(
        df
    )

    side_i_columns = groups[
        ("Vibration", "I")
    ]

    side_ii_columns = groups[
        ("Vibration", "II")
    ]

    side_i = (
        aggregate_refined_side(
            df,
            side_i_columns,
            speed_kmh
        )
    )

    side_ii = (
        aggregate_refined_side(
            df,
            side_ii_columns,
            speed_kmh
        )
    )

    row = {}

    for (
        feature,
        value
    ) in side_i.items():

        row[
            f"refined_side_I_"
            f"{feature}"
        ] = value

    for (
        feature,
        value
    ) in side_ii.items():

        row[
            f"refined_side_II_"
            f"{feature}"
        ] = value

    for feature in side_i:

        row[
            f"refined_difference_"
            f"{feature}"
        ] = (
            side_i[feature]
            - side_ii[feature]
        )

    return row


# ============================================================
# SPATIAL FEATURES
# ============================================================

def rms(signal):

    signal = np.asarray(
        signal,
        dtype=float
    )

    return np.sqrt(
        np.mean(
            signal ** 2
        )
    )


def peak(signal):

    signal = np.asarray(
        signal,
        dtype=float
    )

    return np.max(
        np.abs(signal)
    )


def band_energy(
    signal,
    low,
    high
):

    signal = np.asarray(
        signal,
        dtype=float
    )

    signal = (
        signal
        - np.mean(signal)
    )

    window = np.hanning(
        len(signal)
    )

    fft_values = np.fft.rfft(
        signal * window
    )

    frequencies = np.fft.rfftfreq(
        len(signal),
        d=1 / SAMPLING_RATE
    )

    power = (
        np.abs(
            fft_values
        ) ** 2
    )

    total = np.sum(
        power
    )

    if total <= 0:
        return 0

    mask = (
        (frequencies >= low)
        & (frequencies < high)
    )

    return (
        np.sum(
            power[mask]
        )
        / total
    )


def distribution_features(
    values,
    prefix
):

    values = np.asarray(
        values,
        dtype=float
    )

    return {
        f"{prefix}_mean":
            np.mean(values),

        f"{prefix}_median":
            np.median(values),

        f"{prefix}_max":
            np.max(values),

        f"{prefix}_min":
            np.min(values),

        f"{prefix}_std_across_sensors":
            np.std(values),

        f"{prefix}_p75":
            np.percentile(
                values,
                75
            ),

        f"{prefix}_p90":
            np.percentile(
                values,
                90
            ),
    }


def extract_spatial_features(
    df
):

    sensor_rows = []

    for column in df.columns:

        info = parse_sensor_column(
            column
        )

        if info is None:
            continue

        signal = df[
            column
        ].to_numpy()

        sensor_rows.append({
            "type":
                info["type"],

            "side":
                info["side"],

            "car":
                info["car"],

            "position":
                info["position"],

            "rms":
                rms(signal),

            "peak":
                peak(signal),

            "band_200_300":
                band_energy(
                    signal,
                    200,
                    300
                ),

            "band_400_500":
                band_energy(
                    signal,
                    400,
                    500
                ),

            "band_600_700":
                band_energy(
                    signal,
                    600,
                    700
                ),

            "band_1800_1900":
                band_energy(
                    signal,
                    1800,
                    1900
                ),
        })

    sensors = pd.DataFrame(
        sensor_rows
    )

    output = {}

    for signal_type in [
        "Vibration",
        "Shock"
    ]:

        for side in [
            "I",
            "II"
        ]:

            subset = sensors[
                (
                    sensors["type"]
                    == signal_type
                )
                &
                (
                    sensors["side"]
                    == side
                )
            ]

            metrics = [
                "rms",
                "peak"
            ]

            if (
                signal_type
                == "Vibration"
            ):

                metrics += [
                    "band_200_300",
                    "band_400_500",
                    "band_600_700",
                    "band_1800_1900",
                ]

            for metric in metrics:

                values = subset[
                    metric
                ].to_numpy()

                prefix = (
                    "spatial_"
                    f"{signal_type.lower()}_"
                    f"side_{side}_"
                    f"{metric}"
                )

                output.update(
                    distribution_features(
                        values,
                        prefix
                    )
                )

    car_rms_differences = []
    car_peak_differences = []
    car_band_400_500_differences = []
    car_band_600_700_differences = []

    for car in range(
        1,
        9
    ):

        vibration_car = sensors[
            (
                sensors["type"]
                == "Vibration"
            )
            &
            (
                sensors["car"]
                == car
            )
        ]

        side_i = vibration_car[
            vibration_car[
                "side"
            ] == "I"
        ]

        side_ii = vibration_car[
            vibration_car[
                "side"
            ] == "II"
        ]

        rms_diff = (
            side_i["rms"].mean()
            - side_ii["rms"].mean()
        )

        peak_diff = (
            side_i["peak"].mean()
            - side_ii["peak"].mean()
        )

        band400_diff = (
            side_i[
                "band_400_500"
            ].mean()
            -
            side_ii[
                "band_400_500"
            ].mean()
        )

        band600_diff = (
            side_i[
                "band_600_700"
            ].mean()
            -
            side_ii[
                "band_600_700"
            ].mean()
        )

        output[
            f"car_{car}_"
            "vibration_rms_difference"
        ] = rms_diff

        output[
            f"car_{car}_"
            "vibration_peak_difference"
        ] = peak_diff

        output[
            f"car_{car}_"
            "band_400_500_difference"
        ] = band400_diff

        output[
            f"car_{car}_"
            "band_600_700_difference"
        ] = band600_diff

        car_rms_differences.append(
            rms_diff
        )

        car_peak_differences.append(
            peak_diff
        )

        car_band_400_500_differences.append(
            band400_diff
        )

        car_band_600_700_differences.append(
            band600_diff
        )

    output.update(
        distribution_features(
            car_rms_differences,
            "car_difference_rms"
        )
    )

    output.update(
        distribution_features(
            car_peak_differences,
            "car_difference_peak"
        )
    )

    output.update(
        distribution_features(
            car_band_400_500_differences,
            "car_difference_band_400_500"
        )
    )

    output.update(
        distribution_features(
            car_band_600_700_differences,
            "car_difference_band_600_700"
        )
    )

    return output


# ============================================================
# STFT / TIME-FREQUENCY FEATURES
# ============================================================

def signal_time_frequency_features(
    signal
):

    signal = np.asarray(
        signal,
        dtype=float
    )

    signal = (
        signal
        - np.mean(signal)
    )

    frequencies, _, Zxx = stft(
        signal,
        fs=SAMPLING_RATE,
        window="hann",
        nperseg=1024,
        noverlap=512,
        boundary=None
    )

    power = (
        np.abs(Zxx) ** 2
    )

    output = {}

    for (
        band_name,
        (
            low,
            high
        )
    ) in TF_BANDS.items():

        mask = (
            (frequencies >= low)
            & (frequencies < high)
        )

        if not np.any(
            mask
        ):

            band_over_time = (
                np.zeros(
                    power.shape[1]
                )
            )

        else:

            band_over_time = (
                np.sum(
                    power[
                        mask,
                        :
                    ],
                    axis=0
                )
            )

        output[
            f"tf_{band_name}_mean"
        ] = np.mean(
            band_over_time
        )

        output[
            f"tf_{band_name}_std"
        ] = np.std(
            band_over_time
        )

        output[
            f"tf_{band_name}_max"
        ] = np.max(
            band_over_time
        )

        output[
            f"tf_{band_name}_p90"
        ] = np.percentile(
            band_over_time,
            90
        )

        mean_energy = np.mean(
            band_over_time
        )

        if mean_energy > 0:

            output[
                f"tf_{band_name}_"
                "burst_ratio"
            ] = (
                np.max(
                    band_over_time
                )
                / mean_energy
            )

        else:

            output[
                f"tf_{band_name}_"
                "burst_ratio"
            ] = 0

    return output


def aggregate_side_tf(
    df,
    columns
):

    rows = []

    for column in columns:

        rows.append(
            signal_time_frequency_features(
                df[
                    column
                ].to_numpy()
            )
        )

    temp = pd.DataFrame(
        rows
    )

    output = {}

    for feature in (
        temp.columns
    ):

        values = temp[
            feature
        ].to_numpy()

        output[
            f"{feature}_sensor_mean"
        ] = np.mean(
            values
        )

        output[
            f"{feature}_sensor_std"
        ] = np.std(
            values
        )

        output[
            f"{feature}_sensor_max"
        ] = np.max(
            values
        )

        output[
            f"{feature}_sensor_p90"
        ] = np.percentile(
            values,
            90
        )

    return output


def extract_tf_features(
    df
):

    groups = get_sensor_groups(
        df
    )

    side_i_columns = groups[
        ("Vibration", "I")
    ]

    side_ii_columns = groups[
        ("Vibration", "II")
    ]

    side_i = aggregate_side_tf(
        df,
        side_i_columns
    )

    side_ii = aggregate_side_tf(
        df,
        side_ii_columns
    )

    row = {}

    for (
        feature,
        value
    ) in side_i.items():

        row[
            f"tf_side_I_{feature}"
        ] = value

    for (
        feature,
        value
    ) in side_ii.items():

        row[
            f"tf_side_II_{feature}"
        ] = value

    for feature in side_i:

        row[
            f"tf_difference_{feature}"
        ] = (
            side_i[feature]
            - side_ii[feature]
        )

    return row


# ============================================================
# COMPLETE 699-FEATURE EXTRACTOR
# ============================================================

def extract_features_from_dataframe(
    df
):

    base = extract_base_features(
        df
    )

    speed_kmh = base[
        "speed_kmh"
    ]

    refined = (
        extract_refined_features(
            df,
            speed_kmh
        )
    )

    spatial = (
        extract_spatial_features(
            df
        )
    )

    tf_features = (
        extract_tf_features(
            df
        )
    )

    all_features = {
        **base,
        **refined,
        **spatial,
        **tf_features,
    }

    if len(all_features) != 699:

        raise ValueError(
            "Expected 699 features, "
            f"but extracted "
            f"{len(all_features)}."
        )

    return all_features


def extract_features(
    csv_path
):

    df = pd.read_csv(
        csv_path
    )

    return (
        extract_features_from_dataframe(
            df
        )
    )