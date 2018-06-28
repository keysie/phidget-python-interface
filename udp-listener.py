# Python 3.6
# Encoding: UTF-8
# Date created: 26.06.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import socket
import struct

UDP_IP = "192.168.0.4"
UDP_PORT = 5005
DOUBLES_TO_RECEIVE = 4      # number of double values to expect from one transmission

sock = socket.socket(socket.AF_INET,        # Internet
                     socket.SOCK_DGRAM)     # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    floats = []
    data, addr = sock.recvfrom(1024)        # buffer size is 1024 bytes
    for i in range(0, DOUBLES_TO_RECEIVE):
        floats.append(struct.unpack('d', data[(8*i):(i*8)+8])[0])
    print("received message: ", floats)