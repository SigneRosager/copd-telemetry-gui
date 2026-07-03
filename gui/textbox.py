from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtGui import QFont


class DateListWidget(QWidget):
    def __init__(self, data, patient_id):
        super().__init__()
        self.data = data
        self.patient_id = patient_id

        layout = QVBoxLayout()

        # Add a label on top
        self.label = QLabel("Notes")
        self.label.setFont(QFont("Arial", 12))
        layout.addWidget(self.label)

        # The text box to show dates
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setFont(QFont("Arial", 10))
        layout.addWidget(self.text_box)

        self.setLayout(layout)

    def populate_dates(self):
        df = self.data.get_prediction(self.patient_id)
        model_a_df = df[df['modelId'] == 'MODEL_A']

        date_strings = []
        for dt_obj in model_a_df['date'].unique():
            # Assuming dt_obj is already a datetime.datetime object
            formatted_date = dt_obj.strftime("%d/%m/%Y")
            date_strings.append(f"Exacerbation risk detected on {formatted_date}")

        self.text_box.setPlainText('\n'.join(date_strings))