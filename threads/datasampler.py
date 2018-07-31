# Python 3.6
# Encoding: UTF-8
# Date created: 31.07.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import time
import datetime
from Phidget22.Phidget import *


def LocalErrorCatcher(e):
    print("Phidget Exception: " + str(e.code) + " - " + str(e.details) + ", Exiting...")
    exit(1)


# Convert datetime to excel-compatible serial time
# source: https://stackoverflow.com/a/9574948
def __excel_date(date1):
    temp = datetime.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400) + (float(delta.microseconds) / (86400 * 1000 * 1000))


def thread_method(connected_boards, display_cache, result_cache, interval):
    start_time = time.time()

    while True:
        # write measurements only at selected frequency
        time.sleep(interval - ((time.time() - start_time) % interval))

        timestamp = __excel_date(datetime.datetime.now())
        measurements = []

        for board_index, (serial_no, board) in enumerate(connected_boards.items()):
            for i in range(0, 4):
                try:
                    measurements.append(board.channels[i].getVoltageRatio())
                except PhidgetException as ex:
                    LocalErrorCatcher(ex)

        display_cache.append(measurements)
        result_cache.appendleft((timestamp, measurements))      # writer pops from right
