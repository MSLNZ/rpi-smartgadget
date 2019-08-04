.. _rpi-smartgadget-install:

=======================
Install RPi-SmartGadget
=======================

To set up the Raspberry Pi run the following commands. Instructions for using SSH_
to interface with a Raspberry Pi can be found `here <ssh_instructions_>`_.

The following command is optional *(but recommended)*. It will update the
installed packages on the Raspberry Pi

.. code-block:: console

   sudo apt update && sudo apt upgrade

The following will install the **RPi-SmartGadget** package in a `virtual environment`_
in the ``/home/pi/shtenv`` directory on the Raspberry Pi *(the* ``shtenv`` *directory*
*will be automatically created)*

.. code-block:: console

   git clone https://github.com/MSLNZ/rpi-smartgadget.git
   bash rpi-smartgadget/rpi-setup.sh
   rm -rf rpi-smartgadget

To install **RPi-SmartGadget** on a computer that is not a Raspberry Pi run

.. code-block:: console

   pip install https://github.com/MSLNZ/rpi-smartgadget/archive/master.tar.gz

Alternatively, using the :ref:`msl-package-manager-welcome` run

.. code-block:: console

   msl install rpi-smartgadget

Dependencies
------------

Tested with a Raspberry Pi 3 Model B+ running Raspbian Stretch/Buster.

* Python 3.5+
* :ref:`msl-network-welcome`
* bluepy_ -- only installed on the Raspberry Pi

.. note::

   Although **RPi-SmartGadget** has been tested with a Raspberry Pi to establish
   a Bluetooth connection with a Smart Gadget, any Linux-based operating system
   that bluepy_ supports could be used.

.. _bluepy: https://ianharvey.github.io/bluepy-doc/
.. _virtual environment: https://docs.python.org/3/tutorial/venv.html
.. _SSH: https://www.ssh.com/ssh/
.. _ssh_instructions: https://www.raspberrypi.org/documentation/remote-access/ssh/
