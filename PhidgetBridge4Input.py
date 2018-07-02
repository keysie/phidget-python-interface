import Phidget22.Devices.VoltageRatioInput as Vri
import Phidget22.PhidgetException as PhiEx


class PhidgetBridge4Input(object):
    # -------------- CLASS VARIABLES (SHARED AMONG INSTANCES) ------------
    # NONE SO FAR
    # --------------------------------------------------------------------

    def __init__(self, serial_no):
        # ----------- INSTANCE VARIABLES (UNIQUE FOR EVERY INSTANCE) ----------------

        self.channel_names = ["0", "1", "2", "3"]       # user specified names to ease understanding of results
        self.channel_gain = 7                           # allowed values: 1 (1x), 4 (8x), 5 (16x), 6 (32x), 7 (64x), 8 (128x)
        self.channels = [None, None, None, None]

        # ---------------------------------------------------------------------------

        # Create 4 channels for the 4 bridge inputs
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
            self.serial_number = serial_no
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
        for ch in self.channels:
            if ch is None or not isinstance(ch, Vri.VoltageRatioInput) or not ch.getAttached():
                return False
            else:
                return True

    @property
    def serial_number(self):
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
