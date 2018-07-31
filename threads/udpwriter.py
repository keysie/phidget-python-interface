# Python 3.6
# Encoding: UTF-8
# Date created: 31.07.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import socket
import struct
import sys
import time


def __double_to_bytes(value, target_endianness=sys.byteorder):
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


def __doubles_to_bytes(data, target_endianness=sys.byteorder):
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
            byte_array += __double_to_bytes(value, target_endianness)
    else:
        byte_array += __double_to_bytes(data, target_endianness)

    return byte_array


def thread_method(ip, port, result_cache, interval):
    """
    Method to be executed by writer_thread. Periodically push sampling-results to UDP-target.
    :param ip: IP-address of target computer
    :type ip: IPv4Address
    :param port: Port-number at target computer
    :type port: int
    :param result_cache: Inter-thread buffer for measurement results
    :type result_cache: collections.deque
    :param interval: Time between executions of this method
    :type interval: float
    :return: Nothing
    :rtype: none
    """
    start_time = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        while True:
            # write measurements only at selected frequency
            time.sleep(interval - ((time.time() - start_time) % interval))

            # for as long as possible: pop a sample and send it over udp. if the cache is exhausted wait again.
            while True:
                try:
                    (_, data) = result_cache.pop()  # ignore timestamp, only push results over udp
                    udp_socket.sendto(__doubles_to_bytes(data, 'little'), (ip.exploded, port))
                except IndexError as e:
                    break
