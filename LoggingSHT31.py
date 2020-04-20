from smartgadget import connect, milliseconds_to_datetime, kill_manager

# The IP address of the Raspberry Pi
host = '172.16.14.123'

# The password of the Raspberry Pi (this should be read from a file or from the terminal)
rpi_password = open(r'I:\MSL\Private\Humidity\Laboratory\Research\SMARTGADGET\password.txt').read().strip()

# You could also specify the MAC addresses rather than performing the scan below
mac_addresses = []

try:
    # Connect to the Raspberry Pi and scan for Smart Gadgets
    print('Connecting to the Raspberry Pi...')
    rpi = connect(host=host, rpi_password=rpi_password, assert_hostname=False)
    print('Scanning for Smart Gadgets...')
    mac_addresses = rpi.scan()
    print('Found {} Smart Gadgets'.format(len(mac_addresses)))
    if mac_addresses:
        print('Connecting to {} Smart Gadgets...'.format(len(mac_addresses)))
        rpi.connect_gadgets(mac_addresses, True)

        # Fetch all temperature and humidity logger data.
        #
        # This step can take a very long time (minutes) if there is a lot of data
        # to fetch or if the Bluetooth connection is slow/keeps dropping out.
        # There is no option to display the current status of the request
        # -- see fetch_logged_data_rpi.py which will display status updates.
        for mac_address in mac_addresses:
            print('Fetching data from', mac_address + '...')
            temperatures, humidities = rpi.fetch_logged_data(mac_address)
            n = 1
            nmax = 10
            while any(None in t for t in temperatures) or any(None in h for h in humidities):
                # Attempt to fill in holes in the received data.
                e = sum(t.count(None) for t in temperatures) + sum(h.count(None) for h in humidities)
                print('Filling in {} points of incomplete data, attempt {} of {}'.format(e,n,nmax))
                temperaturestemp, humiditiestemp = rpi.fetch_logged_data(mac_address)
                x = 0
                for i in range(0, min(len(temperatures), (len(humidities)))):
                    if temperatures[i][1] is None and temperaturestemp[i][1] is not None:
                        temperatures[i][1] = temperaturestemp[i][1]
                        x = x + 1
                    if humidities[i][1] is None and humiditiestemp[i][1] is not None:
                        humidities[i][1] = humiditiestemp[i][1]
                        x = x + 1
                print('{} data points filled'.format(x))
                n = n + 1
                if n > nmax:
                    print('Maximum number of attempts reached')
                    break

            print('Fetched {} data points from'.format(len(temperatures)+len(humidities)), mac_address)
            if len(temperatures)-len(humidities) != 0:
                print('lengths are inconsistent')
                continue

            # Save the temperature results (the returned timestamps are in milliseconds)
            with open(mac_address.replace(':', '-') + '_log.csv', 'w') as fp:
                fp.write('timestamp,temperature[C],humidity[%RH]\n')
                for i in range(0,min(len(temperatures),(len(humidities)))):
                    fp.write('{},{},{}\n'.format(milliseconds_to_datetime(temperatures[i][0]), temperatures[i][1], humidities[i][1]))

    # Disconnect from the Raspberry Pi when finished communicating with it
    rpi.disconnect()

except Exception as e:
    rpi = None
    msg = str(e).splitlines()[-1]
    print(msg)
    if msg.endswith('address already in use'):
        print('Killing the Network Manager...')
        kill_manager(host=host, rpi_password=rpi_password)

print('{} Smart Gadget logs fetched'.format(len(mac_addresses)))