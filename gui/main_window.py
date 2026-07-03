from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel
from gui.measurements import Measurements
from gui.predictions import Predictions
from gui.predictions import BarPlot
from gui.textbox import DateListWidget


class MainWindow(QMainWindow):
    def __init__(self, patient_id, data):
        super().__init__()
        self.setWindowTitle(f"Patient {patient_id} Overview")

        self.data = data
        self.patient_id = patient_id
        self.plots = []

        layout = QGridLayout()

        measurement_types = ['pulse', 'saturation', 'diastolic']
        positions = [
            (0, 0, 1, 2),
            (0, 2, 1, 2),
            (1, 0, 1, 2)
        ]
        for i, meas_type in enumerate(measurement_types):
            plot_widget = Measurements(self.data, self.patient_id, meas_type)
            self.plots.append(plot_widget)  # store PlotWidget reference
            row, col, rowspan, colspan = positions[i]
            layout.addWidget(plot_widget, row, col, rowspan, colspan)

        # Sync signal AFTER all plots are created
        for measurement in self.plots:
            vb = measurement.plot.getViewBox()
            vb.sigXRangeChanged.connect(self.sync_plots)
            measurement.update_vertical_line()

        prediction_graph = Predictions(self.data, self.patient_id)
        self.prediction_graph = prediction_graph
        layout.addWidget(prediction_graph, 1, 2, 1, 2)

        bar_chart = BarPlot(self.data, self.patient_id, self.plots[0])
        layout.addWidget(bar_chart, 2, 2, 1, 2)

        # Placeholders
        self.date_list_widget = DateListWidget(self.data, self.patient_id)
        layout.addWidget(self.date_list_widget, 2, 0, 2, 2)
        self.date_list_widget.populate_dates()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def sync_plots(self):
        sender = self.sender()
        x_range = sender.viewRange()[0]
        y_range = sender.viewRange()[1]

        for measurement in self.plots:
            if measurement.plot.getViewBox() is not sender:
                measurement.plot.getViewBox().blockSignals(True)  # Prevent recursive updates

                # Sync x-axis range only
                measurement.plot.getViewBox().setXRange(*x_range, padding=0)
                measurement.plot.getPlotItem().getAxis('bottom').setRange(*x_range)

                # Keep the y-axis fixed
                measurement.plot.getViewBox().setYRange(y_range[0], y_range[1], padding=0)

                measurement.plot.getViewBox().blockSignals(False)

            measurement.update_vertical_line()

        if hasattr(self, 'prediction_graph'):
            prediction_x_range = self.prediction_graph.plot.getViewBox().viewRange()[0]
            if prediction_x_range != x_range:
                self.prediction_graph.plot.getViewBox().setXRange(*x_range, padding=0)
                self.prediction_graph.plot.getPlotItem().getAxis('bottom').setRange(*x_range)
                self.prediction_graph.update_vertical_line()



