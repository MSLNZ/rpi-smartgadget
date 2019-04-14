===============
RPi-SmartGadget
===============

Communicate with a Sensirion SHTxx Smart Gadget.

A Raspberry Pi is used for the Bluetooth Low Energy connectivity and the MSL-Network_ package
allows any computer (independent of the operating system) on the same network as the Raspberry Pi
to request information from the Smart Gadget's that are within the Bluetooth range of the Pi.

Tested with a Raspberry Pi 3 Model B+ running Raspbian GNU/Linux 9 (stretch).

Installation
------------

To set up the Raspberry Pi run the following commands.

The following command is optional, it will update the installed packages on
the Raspberry Pi

.. code-block:: console

   sudo apt update && sudo apt upgrade -y

The following will install the **RPi-SmartGadget** package in a
`virtual environment`_

.. code-block:: console

   git clone https://github.com/MSLNZ/rpi-smartgadget.git
   bash rpi-smartgadget/rpi-setup.sh
   rm -rf rpi-smartgadget/

To install **RPi-SmartGadget** on a computer that is not a Raspberry Pi run

.. code-block:: console

   pip install https://github.com/MSLNZ/rpi-smartgadget/archive/master.tar.gz

Usage
-----

Place a Raspberry Pi in a room where the Smart Gadgets are within Bluetooth range.

On another computer that is on the same network as the Raspberry Pi run

.. code-block:: pycon

   >>> from smartgadget import connect
   >>> rpi = connect(host='IP address of Raspberry Pi', assert_hostname=False)

To find out what can be requested from the SmartGadget Service that is running
on the Raspberry Pi enter

.. code-block:: pycon

    >>> print(rpi.manager(as_yaml=True))
    Manager[raspberrypi:1875]
        attributes:
            identity: () -> dict
            link: (service:str) -> bool
        language: Python 3.5.3
        os: Linux 4.14.98-v7+ armv7l
    Clients [1]:
        Client[192.168.1.71:54137]
            language: Python 3.7.3
            os: Windows 10 AMD64
    Services [1]:
        SmartGadget[localhost:56422]
            attributes:
                battery: (mac_address) -> int
                dewpoint: (mac_address, temperature=None, humidity=None) -> float
                disconnect_service: ()
                humidity: (mac_address) -> float
                info: (mac_address) -> dict
                restart_bluetooth: ()
                rssi: (mac_address) -> int
                scan: (timeout=10, passive=False) -> List[str]
                temperature: (mac_address) -> float
                temperature_humidity: (mac_address) -> Tuple[float]
                temperature_humidity_dewpoint: (mac_address) -> Tuple[float]
            language: Python 3.5.3
            max_clients: -1
            os: Linux 4.14.98-v7+ armv7l

The information about the Manager and which Clients and Services are connected to it
will be shown. The SmartGadget Service indicates that it has the following methods
that can be called: battery, dewpoint, disconnect_service, ...

Next we scan for Smart Gadgets, request the temperature, humidity and dew point and then
disconnect from the Raspberry Pi

.. code-block:: pycon

   >>> mac_addresses = rpi.scan()
   >>> for address in mac_addresses:
   ...    print(address, rpi.temperature_humidity_dewpoint(address))
   fd:cb:17:be:60:37 [22.04, 49.89, 11.23]
   dc:01:f6:33:d7:42 [21.77, 50.27, 10.93]
   >>> rpi.disconnect()

Updating BlueZ
--------------

BlueZ_ is a program that is used to communicate with Bluetooth devices on Linux and
it is what is used on the Raspberry Pi. **RPi-SmartGadget** has been tested with
versions 5.43 and 5.44. Other versions may work as well.

A script is included with **RPi-SmartGadget** that will update your version of
BlueZ_. Since we installed **RPi-SmartGadget** in a `virtual environment`_ on
the Raspberry Pi we must activate the environment

.. code-block:: console

   source shtenv/bin/activate

and then execute

.. code-block:: console

   bluez-update

This will update to BlueZ_ 5.50. To install version 5.47 of BlueZ_ run

.. code-block:: console

   bluez-update 5.47

Dependencies
------------

* Python 3.5+
* MSL-Network_
* paramiko_
* bluepy_

.. _MSL-Network: https://github.com/MSLNZ/msl-network
.. _BlueZ: http://www.bluez.org/
.. _virtual environment: https://docs.python.org/3/tutorial/venv.html
.. _paramiko: http://www.paramiko.org/
.. _bluepy: https://github.com/IanHarvey/bluepy
