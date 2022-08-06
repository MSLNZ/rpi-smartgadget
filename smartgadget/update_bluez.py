"""
BlueZ_ is a program that is used to communicate with Bluetooth devices on Linux.

At the time of writing this script (2020-03-31) the latest version of BlueZ_
was 5.54 and therefore this is the default version when running the
``bluez-update`` console script (see setup.py).

.. _BlueZ: http://www.bluez.org/
"""
import os
import sys
import subprocess

SCRIPT_URL = os.path.join(sys.exec_prefix, 'rpi-smartgadget-bluez-update.sh')

BASH = """#!/bin/bash

# exit on first error
set -e

# install the prerequisites to update BlueZ
sudo apt update
sudo apt install libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev libdbus-glib-1-dev -y

# update BlueZ
sudo systemctl stop bluetooth
wget https://www.kernel.org/pub/linux/bluetooth/bluez-{version}.tar.xz
tar xf bluez-{version}.tar.xz
cd bluez-{version}
./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var --enable-library
make
sudo make install
sudo ln -svf /usr/libexec/bluetooth/bluetoothd /usr/sbin/
sudo install -v -dm755 /etc/bluetooth
sudo install -v -m644 src/main.conf /etc/bluetooth/main.conf
sudo systemctl daemon-reload
sudo systemctl start bluetooth
echo The version of BlueZ is now ...
bluetoothd --version
cd ..
echo It is recommended to reboot the Raspberry Pi

# cleanup
rm -rf bluez-{version}/
rm bluez-{version}.tar.xz
"""


def run():
    """Run the updater.

    Meant to be invoked via the ``bluez-update`` command on the terminal.

    See :ref:`rpi-smartgadget-update-bluez` for more details.
    """

    # latest version of BlueZ is 5.54 (as of 2020-03-31)
    version = sys.argv[-1] if len(sys.argv) > 1 else '5.54'

    try:
        current_version = subprocess.check_output(['bluetoothd', '--version']).decode().strip()
    except subprocess.CalledProcessError:
        action = 'INSTALL'
    else:
        if version == current_version:
            sys.exit('Version {} of BlueZ is already installed.'.format(current_version))
        print('The current version of BlueZ is {}'.format(current_version))
        action = 'DOWNGRADE' if version < current_version else 'UPGRADE'

    out = input('You are going to {} BlueZ to version {} -- Continue [Y/n]? '.format(action, version))
    if out and not out.upper().startswith('Y'):
        sys.exit('Abort.')

    with open(SCRIPT_URL, mode='wt') as fp:
        fp.writelines(BASH.format(version=version))

    subprocess.check_output(['chmod', '+x', SCRIPT_URL])  # make runnable
    subprocess.call(['sudo', SCRIPT_URL])
    os.remove(SCRIPT_URL)
