"""
This example assumes that you are connecting to a Raspberry Pi from
another computer on the network to fetch the logged data.
"""
from smartgadget import connect

# The MAC address of the Smart Gadget you want to download the data from
mac_address = 'ef:ce:43:b4:83:f8'

# Connect to the Raspberry Pi (update the IP address of the Raspberry Pi)
rpi = connect(host='192.168.1.100', assert_hostname=False)

# We will be picky and only allow 1 attempt to perform a Smart Gadget request.
# Increasing this value will decrease the occurrence of getting a
# BTLEDisconnectError or a BrokenPipeError when sending requests.
rpi.set_max_attempts(1)

# Connect to the Smart Gadget. This is optional, you could call
# rpi.fetch_logged_data() without first connecting to the Smart Gadget.
rpi.connect_gadget(mac_address)

# Fetch all temperature logger data.
# The humidity data is also returned but it will be an emtpy list.
#
# This step can take a very long time (minutes) if there is a lot of data
# to fetch or if the Bluetooth connection is slow/keeps dropping out.
# There is no option to display the current status of the request
# -- see fetch_logged_data_rpi.py which will display status updates.
temperatures, humidities = rpi.fetch_logged_data(mac_address, enable_humidity=False)
print('Fetched {} temperature values'.format(len(temperatures)))

# Disconnect from the Raspberry Pi when finished communicating with it
rpi.disconnect()

# Save the temperature results
with open('temperature.csv', 'w') as fp:
    fp.write('run,timestamp,temperature[C]\n')
    for row in temperatures:
        fp.write('{},{},{}\n'.format(*row))
