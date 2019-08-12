"""
This script will set the logger interval for all available Smart Gadgets.

This will delete all values from the memory of each Smart Gadget so that the
timestamps for all Smart Gadgets are in sync.
"""
from time import perf_counter
from smartgadget import connect

# Connect to the Raspberry Pi (update the IP address of the Raspberry Pi)
rpi = connect(host='192.168.1.100', assert_hostname=False)

# Get all available Smart Gadgets
mac_addresses = rpi.scan()

# We connect to all Smart Gadgets now so that the start time of each Smart
# Gadget logger is as close as possible to all other Smart Gadgets. Without
# first connecting to all Smart Gadgets the start time for each Smart Gadget
# would accumulate approximately a 7-second delay (the time it takes to
# connect to a Smart Gadget) compared to the start time of the
# previously-configured Smart Gadget.
rpi.connect_gadgets(mac_addresses)
print('Connected to: {}'.format(rpi.connected_gadgets()))

# Set the logger interval to be 10 seconds (10000 milliseconds)
t0 = perf_counter()
for address in mac_addresses:
    print('Setting the logger interval for {!r}'.format(address))
    rpi.set_logger_interval(address, 10000)
dt = perf_counter() - t0
print('All Smart Gadgets should be in sync to within {:.3f} seconds'.format(dt))

# Disconnect from the Raspberry Pi when finished communicating with it
rpi.disconnect()
