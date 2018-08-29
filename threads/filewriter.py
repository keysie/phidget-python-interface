# Python 3.6
# Encoding: UTF-8
# Date created: 31.07.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import time


def thread_method(filename, result_cache, interval):
    start_time = time.time()

    while True:
        # write measurements only at selected frequency
        time.sleep(interval - ((time.time() - start_time) % interval))

        # pop as many results as possible from shared cache into local cache
        samples = []
        while True:
            try:
                samples.append(result_cache.pop())
            except IndexError as e:
                break

        # prepare one long line to be written to the output-file
        output = ""
        for sample in samples:
            output += str(sample[0])
            for value in sample[1]:
                output += ", " + str(value)
            output += ", " + str(sample[2])     # reference data
            output += "\n"

        # write to file
        with open(filename, 'a') as file:
            file.write(output)
            file.flush()