# Python 3.6
# Encoding: UTF-8
# Date created: 31.07.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

from PyQt5 import QtGui, QtCore
import sampledisplay.ui_main as ui_main
import numpy
import pyqtgraph


class SampleDisplay(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, display_cache, sampling_interval, seconds_before, seconds_after, num_boards, parent=None):
        pyqtgraph.setConfigOption('background', 'w')    # before loading widget
        super(SampleDisplay, self).__init__(parent)
        self.setupUi(self)
        self.btnAdd.clicked.connect(self.update)
        self.grPlot.plotItem.showGrid(True, True, 0.7)
        self.grPlot.plotItem.invertX()
        self.grPlot.plotItem.setXRange(-seconds_before, seconds_after, padding=0)
        self.display_cache = display_cache
        self.seconds_before = seconds_before
        self.seconds_after = seconds_after
        self.sampling_interval = sampling_interval
        self.num_boards = num_boards

    def update(self):
        # get numbers from data
        num_points = len(self.display_cache)
        if isinstance(self.display_cache[0], list):
            num_signals = len(self.display_cache[0])
        else:
            num_signals = 1

        # prepare measured data
        xm = numpy.array(self.display_cache)
        xm = xm * 1000 * 490.5  # convert from mV/V to N

        # prepare time-values for measured data
        tm = numpy.arange(0, self.seconds_after, self.sampling_interval)
        tm = tm[0:num_points]
        tm = tm[::-1]       # invert the order, such that time is counting down instead of up

        measurement_color = pyqtgraph.mkColor('b')
        measurement_pen = pyqtgraph.mkPen(color=measurement_color, width=5)

        if num_signals == 1:
            self.grPlot.plot(tm, xm, pen=measurement_pen, clear=True)
        else:
            for index in numpy.arange(0, num_signals):
                if index == 0:
                    self.grPlot.plot(tm, xm[:, index], pen=measurement_pen, clear=True)
                else:
                    self.grPlot.plot(tm, xm[:, index], pen=measurement_pen, clear=False)

        QtCore.QTimer.singleShot(1, self.update) # QUICKLY repeat