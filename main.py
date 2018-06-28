# Python 3.6
# Encoding: UTF-8
# Date created: 26.06.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import time
import signal
import datetime
import collections
import threading
import os
import shutil
import struct
import ipaddress
import socket

from Phidget22.Devices.Manager import *
from Phidget22.Phidget import *

import PhidgetBridge4Input

file_prefix = ""                                # prefix for filename
sampling_start_time = 0                         # required for sample timing

udp_mode = False                                # set based on input argument '-udp'
udp_ip = None                                   # address of udp-target in case udp-mode is active
udp_port = 0                                    # port @ udp-target in case udp-mode is active

sampling_interval = 0.008                       # sample at 125 Hz
display_interval = 0.2                          # update display at 5 Hz
file_interval = 1.0                             # write results to file at 1 Hz
udp_interval = 0.1                              # push data to udp-target at 10 Hz

result_cache = collections.deque()              # stores results before they are written to a file
display_cache = collections.deque(maxlen=10)    # stores results before they are displayed in console output
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
    # once. Therefore check if the board with the same serial number is already attached.
    if serialNumber not in connected_boards:
        connected_boards[serialNumber] = (PhidgetBridge4Input.PhidgetBridge4Input(serialNumber))
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


# ======== Local helper functions =========

# Convert datetime to excel-compatible serial time
# source: https://stackoverflow.com/a/9574948
def excel_date(date1):
    temp = datetime.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400) + (float(delta.microseconds) / (86400 * 1000 * 1000))


def _double_to_bytes(value, target_endianness=sys.byteorder):
    """
    Convert a single floating point variable to a byte array. If necessary swap endianness for target system.
    :param value: Value to be converted
    :type value: float
    :param target_endianness: Endianness of the target system. Defaults to the endianness of the executing machine.
    Possible values are: 'big' or 'little'.
    :type target_endianness: str
    :return: Bytearray representing the input value in the target endian format
    :rtype: bytearray
    """
    # get byte array in system endianness
    byte_array = bytearray(struct.pack("d", value))

    # swap endianness if necessary
    self_endianness = sys.byteorder
    if self_endianness != target_endianness:
        byte_array = bytes[::-1]

    return byte_array


def doubles_to_bytes(data, target_endianness=sys.byteorder):
    """
    Convert a single floating point number or a list of floating point numbers to a byte array in the target endianness.
    :param data: Value(s) to be converted
    :type data: float or list
    :param target_endianness: Endianness of the target system. Defaults to the endianness of the executing machine.
    Possible values are: 'big' or 'little'.
    :type target_endianness: str
    :return:
    :rtype:
    """
    byte_array = bytearray()

    if isinstance(data, list):
        for value in data:
            byte_array += _double_to_bytes(value, target_endianness)
    else:
        byte_array += _double_to_bytes(data, target_endianness)

    return byte_array


# Cleanup function
def cleanup():
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # ignore sigints while cleaning up
    print("Closing...")
    try:
        manager.close()
    except PhidgetException as e:
        LocalErrorCatcher(e)


# Function to handle sampling
def get_one_sample():
    timestamp = excel_date(datetime.datetime.now())
    measurements = []

    for board_index, (serial_no, board) in enumerate(connected_boards.items()):
        for i in range(0, 4):
            try:
                measurements.append(board.channels[i].getVoltageRatio())
            except PhidgetException as ex:
                LocalErrorCatcher(ex)

    display_cache.append(measurements)
    result_cache.appendleft((timestamp, measurements))      # writer pops from right


# Executed by separate thread to write the result-cache to a file
def file_writer(filename):
    start_time = time.time()

    while True:
        # write measurements only at selected frequency
        time.sleep(file_interval - ((time.time() - start_time) % file_interval))

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
            output += "\n"

        # write to file
        with open(filename, 'a') as file:
            file.write(output)
            file.flush()


def udp_writer(ip, port):
    """
    Method to be executed by writer_thread. Periodically push sampling-results to UDP-target.
    :param ip: IP-address of target computer
    :type ip: IPv4Address
    :param port: Port-number at target computer
    :type port: int
    :return: Nothing
    :rtype: none
    """
    start_time = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        while True:
            # write measurements only at selected frequency
            time.sleep(udp_interval - ((time.time() - start_time) % udp_interval))

            # for as long as possible: pop a sample and send it over udp. if the cache is exhausted wait again.
            while True:
                try:
                    (_, data) = result_cache.pop()  # ignore timestamp, only push results over udp
                    udp_socket.sendto(doubles_to_bytes(data, 'little'), (ip.exploded, port))
                except IndexError as e:
                    break


# Executed by separate thread to display slightly filtered data in command line
def displayer():
    start_time = time.time()

    while True:
        # update screen only at selected frequency
        time.sleep(display_interval - ((time.time() - start_time) % display_interval))

        lines = []      # lines for table
        filtered_results = [sum(i)/len(display_cache) for i in zip(*display_cache)]     # data to display

        # clear screen and print title
        os.system('cls')
        console_width = shutil.get_terminal_size()[0]
        separator = ""
        bar = "======================================================"
        title = "==  Measurement running. Press Ctrl+C to terminate  =="
        for i in range(0, int(console_width/2 - len(title)/2)):
            separator += " "
        print(separator + bar)
        print(separator + title)
        print(separator + bar)
        print("\n")

        for i in range(0, 8):
            if i in [1, 3, 4, 5, 6]:
                lines.append("|")
            elif i in [0, 2, 7]:
                lines.append("+")

            for board_index, (serial_no, board) in enumerate(connected_boards.items()):
                if i == 1:
                    lines[i] += "        " + str(board.serial_number) + "        |"
                elif i in range(3, 7):
                    current_value = filtered_results[4*board_index + (i-3)]
                    lines[i] += " " + str(board.channel_names[i-3]) + ": "
                    if current_value >= 0:
                        lines[i] += " "
                    lines[i] += "{:.9f}".format(current_value) + " mV/V |"
                elif i in [0, 2, 7]:
                    lines[i] += "----------------------+"

        for line in lines:
            print(line)


# ========= Main Code ==========
def main(STATE, udp_mode):

    while True:
        if STATE == "INIT":

            # Check if operating in UDP-mode
            if len(sys.argv) >= 2 and sys.argv[1] == '-udp':
                udp_mode = True

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

            # Wait for user to press ENTER to start sampling
            input("")

            # All done, transition to sampling preparation
            STATE = "PREPARE-FOR-SAMPLING"

        elif STATE == "PREPARE-FOR-SAMPLING":

            # open and prepare file if not in udp mode
            if not udp_mode:

                # Compute filename
                filename = file_prefix + datetime.datetime.now().strftime("%Y-%m-%d %H_%M_%S") + ".csv"

                # Compute header for file (column headers)
                header = "time (excel-format)"
                for serial_nr, board in connected_boards.items():
                    for i in range(0, 4):
                        header = header + ", " + str(board.serial_number) + ":" + str(board.channel_names[i]) + " (mV/V)"

                # Create file and write header
                with open(filename, 'w+') as file:
                    file.write(header + "\n")

            # Set up separate worker-thread that executes the writer function. It will write sampled data from the
            # cache to the file created above in regular intervals to reduce file operations. In normal mode, the
            # thread will execute the file_writer method. In udp-mode, it will execute the udp_writer method.
            if udp_mode:
                target = udp_writer
                args = (udp_ip, udp_port)
            else:
                target = file_writer
                args = (filename,)
            writer_thread = threading.Thread(target=target, daemon=True, args=args)
            writer_thread.start()

            # Set up separate worker-thread that executes the displayer function. It will display slightly filtered
            # (moving average over 20 samples) results in the command line at regular intervals.
            display_thread = threading.Thread(target=displayer, daemon=True)
            display_thread.start()

            sampling_start_time = time.time()
            print("Measurement running (Press CTRL+C to terminate): ")

            STATE = "SAMPLING"

        elif STATE == "SAMPLING":

            get_one_sample()
            time.sleep(sampling_interval - ((time.time() - sampling_start_time) % sampling_interval))

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
        main(STATE, udp_mode)
    except KeyboardInterrupt:
        print("Interrupt caught. Shutting down.")
        cleanup()
        sys.exit(0)
    except SystemExit as e:
        cleanup()
        sys.exit(e)


    print("Phidget Simple Playground (plug and unplug devices)");
    print("Press Enter to end anytime...");
    character = sys.stdin.read(1)



    exit(0)

