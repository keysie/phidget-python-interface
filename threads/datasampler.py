# Python 3.6
# Encoding: UTF-8
# Date created: 31.07.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import time
import datetime
import numpy
import collections
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


def thread_method(connected_boards, desired_force_vector, display_cache, result_cache,
                  reference_cache, gains, seconds_before_measurement, interval):
    start_time = time.time()

    array = numpy.array(desired_force_vector)
    desired_force_t = collections.deque(array[:, 1])
    desired_force_f = collections.deque(array[:, 0])
    last_desired_force_output = 0

    offset_cache = []
    calibrated = False
    static_offsets = [0, 0, 0, 0]

    while True:
        # write measurements only at selected frequency
        time_elapsed = time.time() - start_time
        time.sleep(interval - (time_elapsed % interval))

        timestamp = __excel_date(datetime.datetime.now())
        measurements = []

        # Obtain measurements and store them in the display-chache
        for board_index, (serial_no, board) in enumerate(connected_boards.items()):
            for i in range(0, 4):
                ratio = 0
                try:
                    ratio = board.channels[i].getVoltageRatio()
                except PhidgetException as ex:
                    LocalErrorCatcher(ex)
                measurements.append(ratio * gains[i])

        # automatically calibrate initial offset during first second after start of thread
        if not calibrated:
            offset_cache.append(measurements)
            if time_elapsed >= 1:
                data = numpy.array(offset_cache)
                sums = numpy.sum(axis=0, a=data)
                static_offsets = sums / len(offset_cache)
                calibrated = True
        else:
            measurements -= static_offsets

        display_cache.append(sum(measurements))

        # See if a new desired force value is available for the current time. If not, keep adding the last value to the
        # reference cache
        if time_elapsed > desired_force_t[0]:
            desired_force_t.popleft()
            last_desired_force_output = desired_force_f.popleft()
        reference_cache.append(last_desired_force_output)

        # store measurements also in the result-cache
        reference_index = round(seconds_before_measurement / interval)  # take time offset into account
        result_cache.appendleft((timestamp, measurements, reference_cache[reference_index]))  # writer pops from right
