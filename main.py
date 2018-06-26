# Python 3.6
# Formatting: UTF-8

import time
import sys
import datetime
import decimal
import Phidget22.PhidgetException as PhiEx

import board


bridge = board.Board()

sys.stdout.write("Python 3.6 Phidget Bridge Interface\n")
sys.stdout.write("by Keysie\n\n")

measurements = [0.0, 0.0, 0.0, 0.0]

prefix = input("Specify prefix for filename or press ENTER for no prefix:")
if prefix != '':
    prefix = prefix + " - "

while True:
    if bridge.ready:
        print("\rReady. Press ENTER to begin measurement.")
        input("")
        print("Measurement running (Press CTRL+C to terminate): ")


        filename = prefix + datetime.datetime.now().strftime("%Y-%m-%d %H_%M_%S") + ".csv"
        starttime = datetime.datetime.now()
        with open(filename, 'w+') as file:
            file.write("time (seconds since start), %s (N), %s (N), %s (N), %s (N)\n" % (bridge.channel_names[0],
                                                                         bridge.channel_names[1],
                                                                         bridge.channel_names[2],
                                                                         bridge.channel_names[3]))

        while True:

            timestamp = (datetime.datetime.now() - starttime).total_seconds()

            for i in range(0, 4):
                try:
                    measurements[i] = bridge.channels[i].getVoltageRatio() * 1000 * 490.5
                except PhiEx.PhidgetException as e:
                    print("Phidget Exception % i: % s" % (e.code, e.details))

            sys.stdout.write("\r%s:%0.3EN  %s:%0.3EN  %s:%0.3EN  %s:%0.3EN" % (bridge.channel_names[0], measurements[0],
                                                                           bridge.channel_names[1], measurements[1],
                                                                           bridge.channel_names[2], measurements[2],
                                                                           bridge.channel_names[3], measurements[3]))
            sys.stdout.flush()

            with open(filename, 'a') as file:
                file.write("%s, %0.6E, %0.6E, %0.6E, %0.6E\n" % (timestamp,
                                                                 measurements[0],
                                                                 measurements[1],
                                                                 measurements[2],
                                                                 measurements[3]))

            time.sleep(0.02)    # ~50 Hz measurements

        print('bla')
    else:
        sys.stdout.write("\rWaiting for device to be connected...")
        sys.stdout.flush()

    time.sleep(0.1)
