import sys
from PyQt5.QtWidgets import QApplication
from gui.patient_select import PatientWindow
from data.load_data import PatientData


def run_main_window():
    app = QApplication(sys.argv)

    data = PatientData()
    window = PatientWindow(data)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_main_window()
    