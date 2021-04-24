.. _rpi-smartgadget-install:

=======================
Install RPi-SmartGadget
=======================

Raspberry Pi OS
---------------
This section describe how to set up a Raspberry Pi.

.. note::
   Instructions for using ssh_ to remotely access the terminal of the Raspberry Pi
   can be found `here <ssh_instructions_>`_.

.. tip::
   The following command is optional *but recommended*. It will update the
   installed packages on the Raspberry Pi.

    .. code-block:: console

       sudo apt update && sudo apt upgrade

Make sure that you have git_ installed and then clone the repository

.. code-block:: console

   sudo apt install git
   git clone https://github.com/MSLNZ/rpi-smartgadget.git

The following will install the **RPi-SmartGadget** package in a `virtual environment`_
in the ``/home/pi/shtenv`` directory on the Raspberry Pi *(the* ``shtenv`` *directory*
*will be automatically created)*

.. code-block:: console

   bash rpi-smartgadget/rpi-setup.sh

Windows, Linux or macOS
-----------------------
To install **RPi-SmartGadget** on a computer that is not a Raspberry Pi run

.. code-block:: console

   pip install https://github.com/MSLNZ/rpi-smartgadget/archive/main.tar.gz

Alternatively, using the :ref:`msl-package-manager-welcome` run

.. code-block:: console

   msl install rpi-smartgadget

Dependencies
------------
Tested with a Raspberry Pi 3 Model B+ and a Raspberry Pi 4 Model B
running either Raspbian Stretch or Buster.

* Python 3.5+
* :ref:`msl-network-welcome`
* bluepy_ -- only installed on the Raspberry Pi

.. note::

   Although **RPi-SmartGadget** has been tested with a Raspberry Pi to establish
   a Bluetooth connection with a Smart Gadget, any Linux-based operating system
   that bluepy_ supports could be used.

.. _bluepy: https://ianharvey.github.io/bluepy-doc/
.. _virtual environment: https://docs.python.org/3/tutorial/venv.html
.. _ssh: https://www.ssh.com/ssh/
.. _ssh_instructions: https://www.raspberrypi.org/documentation/remote-access/ssh/
.. _git: https://git-scm.com/
