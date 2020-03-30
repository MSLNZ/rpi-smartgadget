.. _rpi-smartgadget-update-bluez:

============
Update BlueZ
============

BlueZ_ is the program that is used by a Raspberry Pi to communicate with Bluetooth devices.
**RPi-SmartGadget** has been tested with versions 5.43, 5.44, 5.47, 5.50, 5.52 and 5.54.
Other versions may work as well.

A script is included with **RPi-SmartGadget** that will update the version of BlueZ_.
Since the **RPi-SmartGadget** package is :ref:`installed <rpi-smartgadget-install>` in a
`virtual environment`_ called ``shtenv`` on the Raspberry Pi we must first activate the
`virtual environment`_

From the home directory run

.. code-block:: console

   source shtenv/bin/activate

and then execute

.. code-block:: console

   bluez-update

This will update BlueZ_ to version 5.54 *(the latest version at the time of writing the bluez-update script)*.
To install a specific version of BlueZ_ (e.g., version 5.47) run

.. code-block:: console

   bluez-update 5.47

.. _BlueZ: http://www.bluez.org/
.. _virtual environment: https://docs.python.org/3/tutorial/venv.html
