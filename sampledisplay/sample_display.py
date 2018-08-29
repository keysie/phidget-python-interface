# Python 3.6
# Encoding: UTF-8
# Date created: 31.07.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

# Inspired by: https://www.swharden.com/wp/2016-07-31-live-data-in-pyqt4-with-plotwidget/

from PyQt5 import QtGui, QtCore, QtWidgets
import sampledisplay.ui_main as ui_main
import numpy
import pyqtgraph


class SampleDisplay(QtGui.QMainWindow, ui_main.Ui_MainWindow):

    plot_colors = [pyqtgraph.mkColor( 57, 106, 177),        # blue
                   pyqtgraph.mkColor(218, 124,  48),        # orange
                   pyqtgraph.mkColor( 62, 150,  81),        # green
                   pyqtgraph.mkColor(204,  37,  41),        # red
                   pyqtgraph.mkColor( 83,  81,  84),        # grey
                   pyqtgraph.mkColor(107,  76, 154)]        # purple
    # colors taken from: http://ksrowell.com/blog-visualizing-data/2012/02/02/optimal-colors-for-graphs/

    measurement_pens = [pyqtgraph.mkPen(color=plot_colors[0], width=3),
                        pyqtgraph.mkPen(color=plot_colors[1], width=3),
                        pyqtgraph.mkPen(color=plot_colors[2], width=3),
                        pyqtgraph.mkPen(color=plot_colors[3], width=3)]
    reference_pen = pyqtgraph.mkPen(color=plot_colors[5], width=3)

    def __init__(self, display_cache, reference_cache, connected_boards, sampling_interval, seconds_before,
                 seconds_after):
        """
        Create a Qt window with a number of PlotWidgets. The position where the sampled data starts
        at can be controlled with the seconds_before and seconds_after parameters. Data to be displayed must be provided
        through the display_cache deque. Every entry in this queue consists of a multiple of 4 values, belonging to the
        4 channels of the connected boards.
        NOTE: The plot titles can be adjusted by supplying different names for the connected boards via board_names.
        There must be a name for each connected board though, and the ordering of names must match the ordering of
        values in the display_cache.

        :param display_cache: Shared cache of data to be displayed.
        :type display_cache: collections.deque
        :param reference_cache: Shared cache of reference data to be displayed.
        :type reference_cache: collections.deque
        :param connected_boards: Dict of connected boards
        :type connected_boards: dict
        :param sampling_interval: Time between samples (in seconds)
        :type sampling_interval: float
        :param seconds_before: Distance of the sampling data to the right border of its PlotWidget (in seconds)
        :type seconds_before: float
        :param seconds_after: Distance of the sampling data to the left border of its PlotWidget (in seconds)
        :type seconds_after: float
        """
        # initialization of instance variables
        self.display_cache = display_cache
        self.connected_boards = connected_boards
        self.reference_cache = reference_cache
        self.num_boards = len(connected_boards)
        self.seconds_before = seconds_before
        self.seconds_after = seconds_after
        self.sampling_interval = sampling_interval
        self.timerange_measurements = numpy.arange(0, self.seconds_after, self.sampling_interval)[::-1]
        self.timerange_reference = numpy.arange(-self.seconds_before, self.seconds_after, self.sampling_interval)[::-1]

        # initializing
        pyqtgraph.setConfigOption('background', 'w')
        super(SampleDisplay, self).__init__(None)
        self.setupUi(self)

        # dynamically create plots based on the number of sources
        self.plots = []
        for source_index, (source_name, source) in enumerate(connected_boards.items()):
            self.plots.append(pyqtgraph.PlotWidget(self.centralwidget))
            plot = self.plots[source_index]
            self.horizontalLayout.addWidget(plot)
            plot.plotItem.showGrid(True, True, 0.7)
            plot.plotItem.invertX()
            plot.plotItem.setXRange(-seconds_before, seconds_after, padding=0)
            plot.plotItem.setTitle(source_name)

    def update(self):
        """
        Displays data currently stored in data_queues once
        :return: nothing
        :rtype: None
        """

        # iterate over sources
        for source_index in range(0, self.num_boards):

            # iterate over channels in each source
            for channel_index in range(0, 4):

                data = numpy.array(self.display_cache)[:, source_index * 4 + channel_index]

                if channel_index == 0:
                    self.plots[source_index].plot(self.timerange_measurements, data,
                                                  pen=self.measurement_pens[channel_index], clear=True)
                else:
                    self.plots[source_index].plot(self.timerange_measurements, data,
                                                  pen=self.measurement_pens[channel_index], clear=False)

        # plot reference data
        self.plots[0].plot(self.timerange_reference, numpy.array(self.reference_cache),
                           pen=self.reference_pen, clear=False)

        QtCore.QTimer.singleShot(5, self.update)  # QUICKLY repeat (5ms intervals)
