from pathlib import Path

import pandas as pd


class PatientData:
    def __init__(self):
        data_dir = Path(__file__).parent

        # Load synthetic demo data
        self.data_predictions = pd.read_csv(data_dir / "sample_predictions.csv", sep=";")
        self.data_measurements = pd.read_csv(data_dir / "sample_measurements.csv", sep=";")

        # Keep only patients with the demo model predictions
        demo_model_patients = self.data_predictions[
            self.data_predictions["modelId"] == "DEMO_MODEL_001"
        ]["patientID"].unique()

        self.data_predictions = self.data_predictions[
            self.data_predictions["patientID"].isin(demo_model_patients)
        ]

        # Sort by most frequent patient ID
        sorted_predictions = self.data_predictions["patientID"].value_counts().index.tolist()

        # Keep top 3 patients for the demo interface
        self.data_predictions = self.data_predictions[
            self.data_predictions["patientID"].isin(sorted_predictions[:3])
        ]

        selected_ids = self.data_predictions["patientID"].unique()

        self.data_measurements = self.data_measurements[
            self.data_measurements["patientID"].isin(selected_ids)
        ]

        # Convert dates to datetime
        self.data_measurements["date"] = pd.to_datetime(
            self.data_measurements["date"],
            errors="coerce"
        )

        self.data_predictions["date"] = pd.to_datetime(
            self.data_predictions["date"],
            errors="coerce"
        )

        # Remove rows where dates could not be parsed
        self.data_measurements = self.data_measurements.dropna(subset=["date"])
        self.data_predictions = self.data_predictions.dropna(subset=["date"])

        # Create UNIX timestamps for plotting
        self.data_measurements["timestamp"] = self.data_measurements["date"].astype("int64") // 10 ** 9
        self.data_predictions["timestamp"] = self.data_predictions["date"].astype("int64") // 10 ** 9

        # Clean and convert measurement values
        self.data_measurements["value"] = (
            self.data_measurements["value"]
            .astype(str)
            .replace(r"\.00.00$", "", regex=True)
        )

        self.data_measurements["value"] = pd.to_numeric(
            self.data_measurements["value"],
            errors="coerce"
        )

        self.data_predictions["value"] = pd.to_numeric(
            self.data_predictions["value"],
            errors="coerce"
        )

        # Remove rows without usable values
        self.data_measurements = self.data_measurements.dropna(subset=["value"])
        self.data_predictions = self.data_predictions.dropna(subset=["value"])

    def get_prediction(self, patient_id):
        return self.data_predictions[self.data_predictions["patientID"] == patient_id]

    def get_measurement(self, patient_id):
        return self.data_measurements[self.data_measurements["patientID"] == patient_id]