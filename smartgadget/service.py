import subprocess
from typing import List

from msl.network import Service
try:
    from bluepy.btle import Scanner, BTLEDisconnectError
except ImportError:
    pass  # not on the Raspberry Pi

from .smart_gadget import SHT3X, SHTC1


class SmartGadgetService(Service):

    def __init__(self):
        super(SmartGadgetService, self).__init__(name='SmartGadget')
        self._scanner = Scanner()
        self._gadgets_available = {}
        self._gadgets_connected = {}

    def scan(self, timeout=10, passive=False) -> List[str]:
        """Scan for Smart Gadgets that are within Bluetooth range.

        :param float timeout: Scans for devices for the given `timeout` in seconds
        :param bool passive: Use active or passive scanning to obtain more information when connecting.
        :return: A list of MAC addresses of the Smart Gadgets that are available.
        :rtype: list of str
        """
        self._gadgets_available.clear()
        for dev in self._scanner.scan(timeout=timeout, passive=passive):
            name = dev.getValueText(dev.COMPLETE_LOCAL_NAME)
            if name == SHT3X.NAME:
                self._gadgets_available[dev.addr] = (SHT3X, dev)
            elif name == SHTC1.NAME:
                self._gadgets_available[dev.addr] = (SHTC1, dev)
        return list(self._gadgets_available)

    def connect_gadget(self, mac_address, strict=True) -> bool:
        """Connect to the specified Smart Gadget.

        :param str mac_address: The MAC address of the Smart Gadget to connect to.
        :param bool strict: Whether to raise an error if the Smart Gadget could not be connected to.
        :return: Whether the connection was successful.
        :rtype: bool
        """
        failed = self.connect_gadgets([mac_address], strict=strict)[1]
        return len(failed) == 0

    def connect_gadgets(self, mac_addresses, strict=True) -> List[list]:
        """Connect to the specified Smart Gadgets.

        :param list mac_addresses: A list of MAC addresses of the Smart Gadget to connect to.
        :param bool strict: Whether to raise an error if a Smart Gadget could not be connected to.
        :return: A list of MAC addresses of the Smart Gadgets that were successfully connected to
                 and the MAC addresses of the Smart Gadgets that could not be connected to.
        :rtype: list of list
        """
        failed_connections = []
        for mac_address in mac_addresses:
            if mac_address in self._gadgets_available:
                try:
                    self._gadgets_connected[mac_address] = self._connect(mac_address)
                except BTLEDisconnectError:
                    if strict:
                        raise
                    else:
                        failed_connections.append(mac_address)
        return [list(self._gadgets_connected), failed_connections]

    def connected_gadgets(self) -> List[str]:
        """A list of MAC addresses of the Smart Gadgets that are currently connected."""
        return list(self._gadgets_connected)

    def disconnect_gadget(self, mac_address):
        """Disconnect the Smart Gadget with the specified MAC address."""
        gadget = self._gadgets_connected.pop(mac_address, None)
        if gadget:
            try:
                gadget.disconnect()
            except:
                pass

    def disconnect_gadgets(self):
        """Disconnect all Smart Gadgets."""
        for gadget in self._gadgets_connected.values():
            try:
                gadget.disconnect()
            except:
                pass
        self._gadgets_connected.clear()

    def temperature(self, mac_address) -> float:
        """Returns the temperature [deg C] for the specified MAC address."""
        try:
            return self._gadgets_connected[mac_address].temperature()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.temperature()

    def humidity(self, mac_address) -> float:
        """Returns the humidity [%RH] for the specified MAC address."""
        try:
            return self._gadgets_connected[mac_address].humidity()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.humidity()

    def dewpoint(self, mac_address, temperature=None, humidity=None) -> float:
        """Returns the dew point [deg C] for the specified MAC address."""
        try:
            return self._gadgets_connected[mac_address].dewpoint(temperature=temperature, humidity=humidity)
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.dewpoint(temperature=temperature, humidity=humidity)

    def temperature_humidity(self, mac_address) -> List[float]:
        """Returns the temperature [deg C] and humidity [%RH] for the specified MAC address."""
        try:
            return self._gadgets_connected[mac_address].temperature_humidity()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.temperature_humidity()

    def temperature_humidity_dewpoint(self, mac_address) -> List[float]:
        """Returns the temperature [deg C] and humidity [%RH] for the specified MAC address."""
        try:
            return self._gadgets_connected[mac_address].temperature_humidity_dewpoint()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.temperature_humidity_dewpoint()

    def battery(self, mac_address) -> int:
        """Returns the battery level [%] for the specified MAC address."""
        try:
            return self._gadgets_connected[mac_address].battery()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.battery()

    def rssi(self, mac_address) -> int:
        """Received Signal Strength Indication for the last received broadcast from the device.

        This is an integer value measured in dB, where 0 dB is the maximum (theoretical) signal
        strength, and more negative numbers indicate a weaker signal.
        """
        try:
            return self._gadgets_connected[mac_address].rssi()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.rssi()

    def info(self, mac_address) -> dict:
        """Returns a :class:`dict` of all parameters from the Smart Gadget
        for the specified MAC address.

        .. note::

           Calling this method can take approximately 30 seconds.

        """
        try:
            return self._gadgets_connected[mac_address].info()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.info()

    def logger_interval(self, mac_address) -> int:
        """Returns the logger interval, in milliseconds. Only valid for a SHT3X sensor."""
        try:
            return self._gadgets_connected[mac_address].logger_interval()
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.logger_interval()

    def set_logger_interval(self, mac_address, milliseconds):
        """Set the logger interval, in milliseconds. Only valid for a SHT3X sensor."""
        try:
            return self._gadgets_connected[mac_address].set_logger_interval(milliseconds)
        except KeyError:
            with self._connect(mac_address) as sensor:
                return sensor.set_logger_interval(milliseconds)

    def disconnect_service(self):
        """Shutdown the SmartGadget Service and the MSL-Network Manager."""
        self.disconnect_gadgets()
        self._disconnect()

    def restart_bluetooth(self):
        """Restart the bluetooth driver on the Raspberry Pi.

        This can fix scanning issues or connection timeouts.

        This will disconnect all Smart Gadgets that are currently connected.
        """
        self.disconnect_gadgets()
        subprocess.call(['sudo', 'systemctl', 'restart', 'bluetooth'])

    def _connect(self, address):
        cls, scan_entry = self._gadgets_available[address]
        return cls(scan_entry)
