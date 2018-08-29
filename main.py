# Python 3.6
# Encoding: UTF-8
# Date created: 26.06.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT


import datetime
import collections
import threading
import os
import ipaddress
import json
from PyQt5 import QtGui

from Phidget22.Devices.Manager import *
from Phidget22.Phidget import *

import PhidgetBridge4Input

from threads import filewriter, udpwriter, datasampler
from sampledisplay import sample_display
from common import boarddictionary

########### USER CONFIGURABLE VALUES ###########

seconds_before_measurement = 15                 # how many seconds between measurement and appearance of desired value
seconds_after_measurement = 5                   # how much time to be displayed after moment of measurement

display_interval = 0.02                         # update display at 50 Hz
file_interval = 1.0                             # write results to file at 1 Hz
udp_interval = 0.1                              # push data to udp-target at 10 Hz

################################################

file_prefix = ""                                # prefix for filename

udp_mode = False                                # set based on input argument '-udp'
test_mode = False                               # set based on input argument '-test'
udp_ip = None                                   # address of udp-target in case udp-mode is active
udp_port = 0                                    # port @ udp-target in case udp-mode is active

sampling_interval = 0.008                       # sample at 125 Hz
displayed_measurements = round(seconds_after_measurement / sampling_interval)
result_cache = collections.deque()              # stores results before they are written to a file
display_cache = collections.deque(maxlen=displayed_measurements)   # temporary store for displayed measurements
connected_boards = {}                           # dictionary of all connected PhidgetBridge4Input devices

STATE = "INIT"                       # INIT | WAITING | PREPARE-FOR-SAMPLING | SAMPLING | SHUTDOWN | ERROR

# ========== Event Handling Functions ==========


def AttachHandler(self, channel):
    attachedDevice = channel
    serialNumber = attachedDevice.getDeviceSerialNumber()
    deviceName = attachedDevice.getDeviceName()

    # Handle only PhidgetBridge4Input devices. Ignore all others.
    if deviceName != "PhidgetBridge 4-Input":
        return

    # This attach handler is called once per channel, ergo 4 times per board. But each board must be opened only
    # once. Therefore check if the board with the same serial number is already attached. If it is not, read or
    # create the board-dictionary file and if present use the name in the dictionary for the new board.
    if serialNumber not in connected_boards:
        (board_dict, separator) = boarddictionary.read_or_create()

        if str(serialNumber) in board_dict.keys():
            new_board = PhidgetBridge4Input.PhidgetBridge4Input(serialNumber, board_dict[serialNumber], separator)
        else:
            new_board = PhidgetBridge4Input.PhidgetBridge4Input(serialNumber)

        connected_boards[serialNumber] = new_board
        print("Device '" + str(deviceName) + "' attached, Serial Number: " + str(serialNumber))


def DetachHandler(self, channel):
    detachedDevice = channel
    serialNumber = detachedDevice.getDeviceSerialNumber()
    deviceName = detachedDevice.getDeviceName()

    # Handle only PhidgetBridge4Input devices. Ignore all others.
    if deviceName != "PhidgetBridge 4-Input":
        return

    # Same logic as in AttachHandler. Only need to detach a board once.
    if serialNumber in connected_boards:
        connected_boards.pop(serialNumber)
        print("Device '" + str(deviceName) + "' detached, Serial Number: " + str(serialNumber))


# =========== Python-specific Exception Handler ==========

def LocalErrorCatcher(e):
    print("Phidget Exception: " + str(e.code) + " - " + str(e.details) + ", Exiting...")
    exit(1)


# Cleanup function
def cleanup():
    #signal.signal(signal.SIGINT, signal.SIG_IGN)  # ignore sigints while cleaning up
    print("Closing...")
    plt.close('all')
    try:
        manager.close()
    except PhidgetException as e:
        LocalErrorCatcher(e)


# ========= Main Code ==========
def main(STATE, udp_mode, test_mode):

    while True:
        if STATE == "INIT":

            # Check if operating in UDP-mode
            if len(sys.argv) >= 2 and sys.argv[1] == '-udp':
                udp_mode = True

            # Check if operating in TEST-mode
            if len(sys.argv) >= 2 and sys.argv[1] == '-test':
                test_mode = True

            # Change user queries based on mode (udp vs normal)
            if udp_mode:

                # Query user for target ip
                default_ip = "192.168.1.98"
                ip_string = input("Specify target IP or leave blank for default [" + default_ip + "]: ")
                if ip_string != '':
                    print(ip_string)
                    udp_ip = ipaddress.IPv4Address(ip_string)
                else:
                    print(default_ip)
                    udp_ip = ipaddress.IPv4Address(default_ip)
                print("")

                # Query user for target port
                default_port = 25098
                port_string = input("Specify target port or leave blank for default [" + str(default_port) + "]: ")
                if port_string != '':
                    print(port_string)
                    udp_port = int(port_string)
                else:
                    print(str(default_port))
                    udp_port = default_port
                print("")

            else:

                # Query user for file prefix
                file_prefix = input("Specify prefix for filename or press ENTER for no prefix:")
                if file_prefix != '':
                    print(file_prefix)
                    file_prefix = file_prefix + " - "
                else:
                    print("[no prefix]")
                print("")

            # All done, transition to waiting state
            STATE = "WAITING"

        elif STATE == "WAITING":

            print("Ready. Waiting for PhidgetBridge 4-Input devices to be connected.")
            print("Press ENTER to start sampling.")
            print("")

            # Open the manager. From now on it will call the attach and detach callback functions if Phidgets are
            # (dis)connected to/from the computer.
            try:
                manager.open()
            except PhidgetException as e:
                LocalErrorCatcher(e)

            # Set up callbacks for attach and detach
            try:
                manager.setOnAttachHandler(AttachHandler)
                manager.setOnDetachHandler(DetachHandler)
            except PhidgetException as e:
                LocalErrorCatcher(e)

            if test_mode:
                print("Device 'FAKE' attached, Serial Number: 1337")
                connected_boards['1337'] = PhidgetBridge4Input.PhidgetBridge4Input(1337, name='Fake', virtual=True)

            # Wait for user to press ENTER to start sampling
            while True:
                input("")
                if len(connected_boards) == 0:
                    print("Cannot start sampling: No boards are connected!")
                    print("Connect at least one board and try again.")
                else:
                    break

            # All done, transition to sampling preparation
            STATE = "PREPARE-FOR-SAMPLING"

        elif STATE == "PREPARE-FOR-SAMPLING":

            # open and prepare file if not in udp mode
            if not udp_mode:

                # Compute name for csv output file
                filename = file_prefix + datetime.datetime.now().strftime("%Y-%m-%d %H_%M_%S") + ".csv"

                # Compute header for csv output file (column headers)
                header = "time (excel-format)"
                for serial_nr, board in connected_boards.items():
                    for i in range(0, 4):
                        header = header + ", " + board.name + board.name_separator + str(board.channel_names[i]) + " (mV/V)"

                # Create file and write header
                with open(filename, 'w+') as file:
                    file.write(header + "\n")

            # Set up separate worker-thread that executes the writer function. It will write sampled data from the
            # cache to the file created above in regular intervals to reduce file operations. In normal mode, the
            # thread will execute the file_writer method. In udp-mode, it will execute the udp_writer method.
            if udp_mode:
                target = udpwriter.thread_method
                args = (udp_ip, udp_port, result_cache, udp_interval)
            else:
                target = filewriter.thread_method
                args = (filename, result_cache, file_interval)
            writer_thread = threading.Thread(target=target, daemon=True, args=args)
            writer_thread.start()

            # Set up thread to do the actual sampling
            target = datasampler.thread_method
            args = (connected_boards, display_cache, result_cache, sampling_interval)
            sampler_thread = threading.Thread(target=target, daemon=True, args=args)
            sampler_thread.start()

            STATE = "SAMPLING"

        elif STATE == "SAMPLING":
            return
            pass

        elif STATE == "SHUTDOWN":
            pass

        elif STATE == "ERROR":
            pass


if __name__ == '__main__':
    # Create manager
    try:
        manager = Manager()
    except RuntimeError as e:
        print("Runtime Error " + e.details + ", Exiting...\n")
        exit(1)

    # Dick-swinging and license stuff
    os.system('cls')
    print("Python 3.6 Phidget Bridge Interface with multi-board capability")
    print("")
    print("Author: Robert Simpson (robert_zwilling@web.de)")
    print("Copyright: (c) 2018, Robert Simpson")
    print("License: MIT")
    print("")

    # Main loop with keyboard-interrupt (Ctrl+C) handling
    try:
        main(STATE, udp_mode, test_mode)
        app = QtGui.QApplication(sys.argv)
        form = sample_display.SampleDisplay(display_cache, sampling_interval, seconds_before_measurement, seconds_after_measurement, len(connected_boards))
        form.show()
        form.update()  # start with something
        app.exec_()
    except KeyboardInterrupt:
        print("Interrupt caught. Shutting down.")
        cleanup()
        sys.exit(0)
    except SystemExit as e:
        cleanup()
        sys.exit(e)

    print("Window closed. Shutting down.")
    exit(0)
