# Phidget Python Interface

A software package written in Python 3 that is designed to facilitate the process of recording data using one or more [PhidgetBridge 4-Input](https://www.phidgets.com/?tier=3&catid=98&pcid=78&prodid=1027) devices connected to the executing computer via USB.

## Installation
Unfortunately, the installation process depends on the type of hardware you are using, as well as the OS. The most common cases are described below. Note that the described procedures are not the only way to achieve a working environment. Because I am lazy I will for example not go into the details of configuring all this with virtual python environments. Think of the instructions as the vanilla version.

### Windows x86 (32bit) and x86-64 (64 bit)

1. Install Python 3 using the appropriate Windows Installer from [python.org](https://www.python.org/downloads/release/python-370/). Latest tested version is 3.7.0.

2. Install Phidget USB-Driver using the [manufaturer's installer package](https://www.phidgets.com/docs/OS_-_Windows#Quick_Downloads).

3. Use pip to install the required Python packages. The easiest way to do this is by running ```pip install -r requirements.txt```. This will install specific versions of the packages that have been tested by us devs. You can however also be brave and install the packages using pip manually with other versions.
__NOTE__: It's Windows, so you'll have to run the console you're installing from as administrator.

*If anyone ever gets to test this, please let me know if I forgot something.*

### Raspbian Strech on Raspberry Pi 

1. Install Python 3 using ``sudo apt-get install python3``

2. Install Phidget USB-Driver using this more involved procedure which is also documented on the [Phidget website](https://www.phidgets.com/docs/OS_-_Linux#Debian_Install):
    1. Become root by executing ``sudo su``
    5. as root, do ```wget -qO- http://www.phidgets.com/gpgkey/pubring.gpg | apt-key add -```
    6. then, still as root, do ```echo 'deb http://www.phidgets.com/debian stretch main' > /etc/apt/sources.list.d/phidgets.list```
    7. as root, type ```exit``` to return to normal user shell
    8. as normal user again, run ```sudo apt-get update```
    9. and```sudo apt-get install libphidget22```

3. Manually install PyQt5 and numpy using ```sudo apt-get install qt5-default pyqt5-dev pyqt5-dev-tools python3-numpy```

4. Also manually install mock and pyqtgraph using pip3:
```pip3 install mock pyqtgraph```

You can install numpy using pip3 instead of apt-get, but if you do this then __you must run pip3 as root using ``sudo``__. If you don't you will get error messages about missing libraries. PyQt5 does not currently provide a wheels package for ARM, thus no luck there using pip3.

### Ubuntu x86 and x86-64

1. same as for Raspbian
2. almost the same, except replace *stretch* in 2.3 with
    * *xenial* for 16.04
    * *bionic* for 18.04

3. run ```sudo pip3 install -r requirements.txt```. Note the __sudo__!

## Usage

For normal use execute ``python3 ./main.py``. This will start the script in normal mode, meaning data is recorded in the background, reference and measurement data will be displayed.