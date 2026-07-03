from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


np.random.seed(42)

DATA_DIR = Path(__file__).parent

MEASUREMENTS_OUTPUT = DATA_DIR / "sample_measurements.csv"
PREDICTIONS_OUTPUT = DATA_DIR / "sample_predictions.csv"


def generate_measurements():
    """
    Generate synthetic telemetry measurements for demo patients.

    Columns match the original project structure:
    measurementID;date;patientID;type;value
    """
    patients = ["DEMO_001", "DEMO_002", "DEMO_003"]
    start_time = datetime(2024, 1, 1, 8, 0, 0)

    rows = []
    measurement_id = 1

    for patient_id in patients:
        patient_offset = np.random.randint(-5, 6)

        for hour in range(72):  # 3 days of hourly measurements
            timestamp = start_time + timedelta(hours=hour)

            pulse = int(np.random.normal(82 + patient_offset, 6))
            saturation = round(np.random.normal(95, 1.5), 1)
            diastolic = int(np.random.normal(75 + patient_offset, 5))

            # Keep values in realistic-ish ranges
            pulse = max(55, min(pulse, 120))
            saturation = max(88, min(saturation, 100))
            diastolic = max(55, min(diastolic, 95))

            rows.extend([
                {
                    "measurementID": measurement_id,
                    "date": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "patientID": patient_id,
                    "type": "pulse",
                    "value": pulse,
                },
                {
                    "measurementID": measurement_id + 1,
                    "date": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "patientID": patient_id,
                    "type": "saturation",
                    "value": saturation,
                },
                {
                    "measurementID": measurement_id + 2,
                    "date": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "patientID": patient_id,
                    "type": "diastolic",
                    "value": diastolic,
                },
            ])

            measurement_id += 3

    measurements = pd.DataFrame(rows)
    measurements.to_csv(MEASUREMENTS_OUTPUT, sep=";", index=False)

    return measurements


def generate_predictions(measurements):
    """
    Generate synthetic prediction outputs.

    Columns match the original project structure:
    predictionID;patientID;date;parametersId;modelId;value;prediction;measurements
    """
    patients = measurements["patientID"].unique()

    rows = []
    prediction_id = 1

    for patient_id in patients:
        patient_measurements = measurements[measurements["patientID"] == patient_id].copy()
        patient_measurements["date"] = pd.to_datetime(patient_measurements["date"])

        prediction_times = sorted(patient_measurements["date"].unique())[12::12]

        for timestamp in prediction_times:
            recent = patient_measurements[
                (patient_measurements["date"] <= timestamp)
                & (patient_measurements["date"] > timestamp - pd.Timedelta(hours=12))
            ]

            recent_pulse = recent[recent["type"] == "pulse"]["value"].mean()
            recent_sat = recent[recent["type"] == "saturation"]["value"].mean()
            recent_dia = recent[recent["type"] == "diastolic"]["value"].mean()

            # Synthetic risk score, loosely based on abnormal-ish values
            risk_score = 0.20
            risk_score += max(0, (recent_pulse - 85) / 100)
            risk_score += max(0, (94 - recent_sat) / 20)
            risk_score += max(0, (recent_dia - 78) / 100)
            risk_score += np.random.normal(0, 0.03)

            risk_score = round(float(max(0.01, min(risk_score, 0.95))), 3)

            prediction_label = "high_risk" if risk_score >= 0.5 else "low_risk"

            measurement_ids = recent["measurementID"].astype(str).tolist()

            rows.append({
                "predictionID": prediction_id,
                "patientID": patient_id,
                "date": pd.to_datetime(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "parametersId": "DEMO_PARAMETERS_001",
                "modelId": "DEMO_MODEL_001",
                "value": risk_score,
                "prediction": prediction_label,
                "measurements": ",".join(measurement_ids),
            })

            prediction_id += 1

    predictions = pd.DataFrame(rows)
    predictions.to_csv(PREDICTIONS_OUTPUT, sep=";", index=False)

    return predictions


if __name__ == "__main__":
    measurements_df = generate_measurements()
    predictions_df = generate_predictions(measurements_df)

    print(f"Saved synthetic measurements to: {MEASUREMENTS_OUTPUT}")
    print(f"Saved synthetic predictions to: {PREDICTIONS_OUTPUT}")
    print(f"Measurements rows: {len(measurements_df)}")
    print(f"Predictions rows: {len(predictions_df)}")