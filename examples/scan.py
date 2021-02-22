#!/home/pi/shtenv/bin/python
"""
Scan for Bluetooth devices.

This example assumes that you are directly running the script on a Raspberry Pi.

You must execute this script as the root user in order to have access to
the Bluetooth drivers.

First, make this script executable

  $ chmod +x scan.py

Next, execute the script

  $ sudo ./scan.py

"""
import smartgadget

for dev in smartgadget.scan():
    print('Device {!r} ({}), RSSI={} dB'.format(dev.addr, dev.addrType, dev.rssi))
    for adtype, desc, value in dev.getScanData():
        print('  {} = {}'.format(desc, value))
