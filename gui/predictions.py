from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QFont
from pyqtgraph import AxisItem
from PyQt5.QtCore import Qt
import datetime
import pyqtgraph as pg


class DateAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime("%d/%m/%y") for value in values]


class PercentAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{int(value)}%" for value in values]


class Predictions(QWidget):
    def __init__(self, data, patient_id):
        super().__init__()

        # Store data for later use
        self.data = data
        self.patient_id = patient_id

        # Plot design
        self.plot = pg.PlotWidget(axisItems={'bottom': DateAxisItem(orientation='bottom')})
        self.plot.setBackground('w')
        self.plot.setTitle('Prediction Value')

        # Create plot layout
        layout = QVBoxLayout()
        layout.addWidget(self.plot)
        self.setLayout(layout)

        self.init_plot(data, patient_id)

    def init_plot(self, data, patient_id):

        df = self.data.get_prediction(self.patient_id)
        df = df[df['patientID'] == patient_id]

        # Drop NaN 'value' in predictions
        df = df.dropna(subset='value')

        recent_timestamp = df['timestamp'].max()
        df.columns = df.columns.str.strip()

        x = df['timestamp'].to_numpy()
        y = df['value'].to_numpy()

        self.plot.plot(x, y, pen='skyblue')
        self.plot.plot(x, y, symbol='o', symbolSize=5, pen=None, symbolBrush='skyblue')

        self.plot.getViewBox().setMouseEnabled(x=True, y=False)

        # Y axis setup
        if len(y) > 0:
            y_min, y_max = min(y) - .2, max(y) + .2
            self.plot.setYRange(y_min, y_max, padding=0)
            self.plot.setLimits(yMin=y_min, yMax=y_max)

        # X axis setup (14-day range)
        if len(x) > 0:
            end_time = recent_timestamp
            start_time = end_time - (14 * 24 * 60 * 60)
            self.plot.setXRange(start_time, end_time, padding=0)

        self.vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('k', style=Qt.DashLine), movable=False)
        self.plot.addItem(self.vline, ignoreBounds=True)

    def update_vertical_line(self):
        x_range = self.plot.getViewBox().viewRange()[0]
        center_x = (x_range[0] + x_range[1]) / 2
        self.vline.setPos(center_x)


class BarPlot(QWidget):
    def __init__(self, data, patient_id, find_center):
        super().__init__()

        # Store data for later use
        self.data = data
        self.patient_id = patient_id
        self.find_center = find_center
        self.closest_model_id = None

        self.pulse_pct = 0
        self.spo2_pct = 0
        self.dbp_pct = 0

        # Demo-only contribution weights.
        # These are synthetic and do not represent the original model parameters.
        self.demo_model_id = "DEMO_MODEL_001"
        self.weight_pulse = 0.012
        self.weight_spo2 = 0.75
        self.weight_dbp = 0.08


        # Create Bar chart
        self.bar = pg.PlotWidget()
        self.bar.setBackground('w')
        self.bar.setTitle('Relative Contribution to Alert Output')

        # Create plot layout
        layout = QVBoxLayout()
        layout.addWidget(self.bar)
        self.setLayout(layout)

        # Set up signal listener for dynamic updates
        self.find_center.plot.getViewBox().sigXRangeChanged.connect(self.update_center_timestamp)

        # Initialize bar plot once when the widget is created
        self.find_center.update_vertical_line()
        self.update_center_timestamp()

    def init_bar(self):
        bar_data = [self.pulse_pct, self.spo2_pct, self.dbp_pct]
        labels = ['Pulse', 'Saturation', 'Blood Pressure']
        x = [0, 1, 2]

        self.bar.clear()

        # If there's no valid data to display
        if not any(bar_data) or any(val is None or val != val for val in bar_data):  # Check for 0s or NaNs
            msg = pg.TextItem("Not enough data available", anchor=(0.5, 0.5), color='black')
            msg.setFont(QFont('Arial', 16))
            msg.setPos(1, 0.5)
            self.bar.addItem(msg)

            self.bar.setYRange(0, 1)
            ax = self.bar.getAxis('bottom')
            ax.setTicks([list(zip(x, labels))])
            return

        bg = pg.BarGraphItem(x=x, height=bar_data, width=0.6, brush='skyblue')
        self.bar.addItem(bg)

        ax = self.bar.getAxis('bottom')
        ax.setTicks([list(zip(x, labels))])

        # Add text labels on top of bars
        for xpos, height in zip(x, bar_data):
            text = f"{height:.1f}%"  # Format with one decimal place and percent sign
            label = pg.TextItem(text, anchor=(0.5, -0.5), color='black')
            label.setPos(xpos, height)  # +0.3 centers label on bar, height positions it above
            self.bar.addItem(label)

        # Set y-range to fit labels a bit above max bar height
        y_max = max(bar_data) if bar_data else 1
        self.bar.setYRange(0, y_max * 1.2)

    def update_center_timestamp(self):
        center_timestamp = self.find_center.vline.pos().x()
        self.locate_closest_timestamp(center_timestamp)

    def locate_closest_timestamp(self, center_timestamp):
        df = self.data.get_prediction(self.patient_id).copy()

        # Calculate absolute difference to center timestamp
        df['timestamp_diff'] = (df['timestamp'] - center_timestamp).abs()

        # Find row with smallest difference
        self.closest_row = df.loc[df['timestamp_diff'].idxmin()]

        # Get modelID from that row
        self.closest_model_id = self.closest_row['modelId']
        self.closest_row = self.closest_row

        self.calculate_risk(center_timestamp)

    def calculate_risk(self, center_timestamp):
        if self.closest_model_id == self.demo_model_id:
            meas_id = [mid.strip() for mid in self.closest_row['measurements'].split(',')]

            measurements_df = self.data.get_measurement(self.patient_id)

            matching_measurements = measurements_df[
                measurements_df['measurementID'].astype(str).isin(meas_id)
            ]

            pulse_mean = matching_measurements[
                matching_measurements['type'] == 'pulse'
                ]['value'].mean()

            dbp_var = matching_measurements[
                matching_measurements['type'] == 'diastolic'
                ]['value'].var()

            spo2_var = matching_measurements[
                matching_measurements['type'] == 'saturation'
                ]['value'].var()

            if any(val is None or val != val for val in [pulse_mean, dbp_var, spo2_var]):
                self.pulse_pct = self.spo2_pct = self.dbp_pct = 0
            else:
                # Synthetic demo contributions.
                # These values illustrate the interface only and do not represent
                # the original prediction model.
                pulse_contribution = abs(self.weight_pulse * pulse_mean)
                spo2_contribution = abs(self.weight_spo2 * spo2_var)
                dbp_contribution = abs(self.weight_dbp * dbp_var)

                total_contrib = (
                        pulse_contribution
                        + spo2_contribution
                        + dbp_contribution
                )

                self.pulse_pct = pulse_contribution / total_contrib * 100
                self.spo2_pct = spo2_contribution / total_contrib * 100
                self.dbp_pct = dbp_contribution / total_contrib * 100

            print(
                f"Pulse %: {self.pulse_pct:.1f}, "
                f"Saturation %: {self.spo2_pct:.1f}, "
                f"Blood Pressure %: {self.dbp_pct:.1f}"
            )

        else:
            self.pulse_pct = self.spo2_pct = self.dbp_pct = 0

        self.init_bar()
