from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolTip
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph import AxisItem
import datetime


class DateAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime("%d/%m/%y") for value in values]


class Measurements(QWidget):
    def __init__(self, data, patient_id, measurement_type):
        super().__init__()
        self.plot = pg.PlotWidget(axisItems={'bottom': DateAxisItem(orientation='bottom')})
        self.plot.setBackground('w')
        self.plot.setTitle(measurement_type.capitalize())

        layout = QVBoxLayout()
        layout.addWidget(self.plot)
        self.setLayout(layout)

        self.init_plot(data, patient_id, measurement_type)

    def init_plot(self, data, patient_id, measurement_type):
        label_map = {
            'pulse': ('Pulse', 'BPM'),
            'saturation': ('Oxygen Saturation', '%'),
            'diastolic': ('Blood Pressure', 'mmHg')}
        color = 'skyblue'
        label, unit = label_map.get(measurement_type, ('Value', ''))

        df = data.get_measurement(patient_id)
        recent_timestamp = df['timestamp'].max()
        df = df[(df['type'] == measurement_type) & (df['patientID'] == patient_id)]
        df.columns = df.columns.str.strip()

        x = df['timestamp'].to_numpy()
        y = df['value'].to_numpy()

        # 1. Draw line plot
        self.plot.plot(x, y, pen=color)
        self.plot.plot(x, y, symbol='o', symbolSize=5, pen=None, symbolBrush=color)

        self.plot.getViewBox().setMouseEnabled(x=True, y=False)

        # Y axis setup
        if len(y) > 0:
            y_min, y_max = min(y) - 5, max(y) + 5
            self.plot.setYRange(y_min, y_max, padding=0)
            self.plot.setLimits(yMin=y_min, yMax=y_max)
            self.plot.setLabel('left', label, units=unit)

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


