import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from gui.main_window import MainWindow


class PatientWindow(QMainWindow):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("Select a Patient")
        self.detail_windows = []

        self.data = data  # Store your PatientData instance
        layout = QVBoxLayout()

        patient_ids = list(set(self.data.data_predictions["patientID"]))

        # Add buttons for each patient
        for patient_id in patient_ids:
            btn = QPushButton(f"Patient {patient_id}")
            btn.clicked.connect(lambda _, pid=patient_id: self.open_main_window(pid))
            layout.addWidget(btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_main_window(self, patient_id):
        main_window = MainWindow(patient_id, self.data)
        main_window.show()
        self.detail_windows.append(main_window)
