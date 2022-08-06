"""
Sample script to log the battery, temperature, humidity and dew point from all
available Smart Gadgets to separate CSV files. The MAC address of a Smart Gadget
is used as the name of the file.

Sometimes the number of Smart Gadgets discovered during a Bluetooth scan is
less than the number expected. This example script does not rescan until the
expected number are found. Alternatively, if you know the MAC addresses of the
Smart Gadgets that you want to log then you could specify the MAC addresses
in a list and not perform the Bluetooth scan.
"""
import os
import time
from datetime import datetime

from smartgadget import connect, kill_manager

# The IP address of the Raspberry Pi
host = '192.168.1.100'

# The password of the Raspberry Pi (this should be read from a file or from the terminal)
rpi_password = '<PASSWORD>'

# The folder to save the data to (default value is the current working directory)
save_dir = ''

# You could also specify the MAC addresses rather than performing the scan below
mac_addresses = []

# The number of seconds to wait after fetching the data from all Smart Gadgets
sleep = 10

# Initialize these parameters (they don't need to be changed)
files = {}
rpi = None

while True:
    try:
        if rpi is None:
            # Connect to the Raspberry Pi and scan for Smart Gadgets
            print('Connecting to the Raspberry Pi...')
            rpi = connect(host=host, rpi_password=rpi_password, assert_hostname=False)
            print('Scanning for Smart Gadgets...')
            mac_addresses = rpi.scan()
            print('Found {} Smart Gadgets'.format(len(mac_addresses)))
            if not mac_addresses:
                break
            print('Connecting to {} Smart Gadgets...'.format(len(mac_addresses)))
            rpi.connect_gadgets(mac_addresses)
            for address in mac_addresses:
                files[address] = os.path.join(save_dir, address.replace(':', '-') + '.csv')
                if not os.path.isfile(files[address]):
                    print('Create logging file {!r}'.format(files[address]))
                    with open(files[address], mode='wt') as f:
                        f.write('Timestamp,Battery[%],Temperature[C],Humidity[%RH],Dewpoint[C]\n')

        for address in mac_addresses:
            # Fetch the data and append to the appropriate file
            battery = rpi.battery(address)
            values = rpi.temperature_humidity_dewpoint(address)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print('{} [{}] {:3d} {:.3f} {:.3f} {:.3f}'.format(now, address, battery, *values))
            with open(files[address], mode='at') as fp:
                fp.write('{},{},{},{},{}\n'.format(now, battery, *values))

        time.sleep(sleep)

    except KeyboardInterrupt:
        print('CTRL+C received...')
        break

    except Exception as e:
        rpi = None
        msg = str(e).splitlines()[-1]
        print(msg)
        if msg.endswith('address already in use'):
            print('Killing the Network Manager...')
            kill_manager(host=host, rpi_password=rpi_password)

# Must wait for the previous request to finish before sending the disconnect request
try:
    rpi.wait()
except:
    pass

# Disconnect from the Raspberry Pi
try:
    rpi.disconnect()
except:
    pass

print('Disconnected from the Raspberry Pi')
