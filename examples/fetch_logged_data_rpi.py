#!/home/pi/shtenv/bin/python
"""
This example assumes that you are directly running the script on a Raspberry Pi.

You must execute this script as the root user in order to have access to
the Bluetooth drivers.

First, make this script executable

  $ chmod +x fetch_logged_data_rpi.py

Next, execute the script

  $ sudo ./fetch_logged_data_rpi.py

"""
import logging
from smartgadget import SHT3XService

# This allows you to see some status messages displayed to the terminal
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)-7s] %(message)s')

# The MAC address of the Smart Gadget you want to download the data from
mac_address = 'ef:ce:43:b4:83:f8'

# Create an instance of the Smart Gadget Service
s = SHT3XService()

# Fetch all available temperature and humidity logger data.
# Perform this 2 times to reduce missing data packets during the Bluetooth download.
# This step can take a very long time (minutes) if there is a lot of data
# to fetch or if the Bluetooth connection is slow/keeps dropping out.
temperatures, humidities = s.fetch_logged_data(mac_address, num_iterations=2, as_datetime=True)

# Disconnect from the Smart Gadget when finished communicating with it
s.disconnect_gadgets()

# Save the results
with open('temperature.csv', 'w') as fp:
    fp.write('timestamp,temperature[C]\n')
    for row in temperatures:
        fp.write('{},{}\n'.format(*row))

with open('humidity.csv', 'w') as fp:
    fp.write('timestamp,humidity[%RH]\n')
    for row in humidities:
        fp.write('{},{}\n'.format(*row))
