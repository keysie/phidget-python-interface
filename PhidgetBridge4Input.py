# Python 3.6
# Encoding: UTF-8
# Date created: 26.06.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import time
from mock import Mock
import Phidget22.Devices.VoltageRatioInput as Vri
import Phidget22.PhidgetException as PhiEx


class PhidgetBridge4Input(object):
    # -------------- CLASS VARIABLES (SHARED AMONG INSTANCES) ------------
    # NONE SO FAR
    # --------------------------------------------------------------------

    def __init__(self, serial_no, virtual=False):
        # ----------- INSTANCE VARIABLES (UNIQUE FOR EVERY INSTANCE) ----------------

        self.channel_names = ["0", "1", "2", "3"]       # user specified names to ease understanding of results
        self.channel_gain = 7                           # allowed values: 1 (1x), 4 (8x), 5 (16x), 6 (32x), 7 (64x), 8 (128x)
        self.channels = [None, None, None, None]
        self.virtual = virtual                          # instance only simulates hardware

        # ---------------------------------------------------------------------------

        # Create 4 channels for the 4 bridge inputs
        if self.virtual:
            self.channels[0] = Mock(['getVoltageRatio'])
            self.channels[0].getVoltageRatio = lambda: (((time.time() * 10) % 50) - 25)
            self.channels[1] = Mock(['getVoltageRatio'])
            self.channels[1].getVoltageRatio = lambda: ((((time.time() * 10) + 12.5) % 50) - 25)
            self.channels[2] = Mock(['getVoltageRatio'])
            self.channels[2].getVoltageRatio = lambda: ((((time.time() * 10) + 25) % 50) - 25)
            self.channels[3] = Mock(['getVoltageRatio'])
            self.channels[3].getVoltageRatio = lambda: ((((time.time() * 10) + 37.5) % 50) - 25)
        else:
            try:
                self.channels[0] = Vri.VoltageRatioInput()
                self.channels[1] = Vri.VoltageRatioInput()
                self.channels[2] = Vri.VoltageRatioInput()
                self.channels[3] = Vri.VoltageRatioInput()

            except RuntimeError as e:
                print("Error creating channels: %s" % e.args)
                exit(1)

            # Configure all four channels
            try:
                for ch, i in list(zip(self.channels, range(0, 4))):
                    ch.setOnAttachHandler(self._attach_handler)
                    ch.setDeviceSerialNumber(serial_no)
                    ch.setChannel(i)
                    ch.open()

            except PhiEx.PhidgetException as e:
                print("Phidget Exception % i: % s" % (e.code, e.details))
                exit(1)

    @property
    def ready(self):
        if self.virtual:
            return True

        for ch in self.channels:
            if ch is None or not isinstance(ch, Vri.VoltageRatioInput) or not ch.getAttached():
                return False
            else:
                return True

    @property
    def serial_number(self):
        if self.virtual:
            return 1337

        serials = [0, 1, 2, 3]
        for i, ch in enumerate(self.channels):
            try:
                serials[i] = ch.getDeviceSerialNumber()
            except PhiEx.PhidgetException as e:
                print("Phidget Exception % i: % s" % (e.code, e.details))
                exit(1)
        if len(set(serials)) == 1:
            return serials[0]
        else:
            print('Not all channels have same serial number. Terminating.')
            exit(1)

    def _attach_handler(self, channel):
        channel.setDataInterval(8)
        channel.setBridgeGain(self.channel_gain)
