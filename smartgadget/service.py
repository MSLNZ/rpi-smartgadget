"""
The base :class:`~msl.network.service.Service` class.
"""
import subprocess
from datetime import datetime
from typing import List, Tuple

from msl.network import Service
try:
    from bluepy.btle import Scanner, BTLEDisconnectError
except ImportError:  # then not on the Raspberry Pi
    Scanner, BTLEDisconnectError = object, object


class SmartGadgetService(Service):

    def __init__(self, cls):
        super(SmartGadgetService, self).__init__(name=cls.DEVICE_NAME)
        self.DEVICE_NAME = cls.DEVICE_NAME
        self.CLS = cls
        self._retries = 5
        self._scanner = Scanner()
        self._gadgets_available = {}
        self._gadgets_connected = {}

    def max_retries(self) -> int:
        """Returns the maximum number of times to try to connect or read/write data from/to a Smart Gadget.

        Since the Bluetooth connection can drop unexpectedly, this provides the opportunity
        to re-connect or re-send a request to the Smart Gadget.
        """
        return self._retries

    def set_max_retries(self, value: int):
        """Set the maximum number of times to try to read/write data from/to a Smart Gadget."""
        self._retries = int(value)

    def scan(self, timeout=10, passive=False) -> List[str]:
        """Scan for Smart Gadgets that are within Bluetooth range.

        :param float timeout: The number of seconds to scan for Smart Gadgets.
        :param bool passive: Use active (to obtain more information when connecting) or passive scanning.
        :return: A list of MAC addresses of the Smart Gadgets that are available.
        :rtype: list of str
        """
        self._gadgets_available.clear()
        for d in self._scanner.scan(timeout=timeout, passive=passive):
            if d.getValueText(d.COMPLETE_LOCAL_NAME) == self.DEVICE_NAME:
                self._gadgets_available[d.addr] = d
        return list(self._gadgets_available)

    def connect_gadget(self, mac_address: str, strict=True) -> bool:
        """Connect to the specified Smart Gadget.

        It is not necessary to call this method to connect to a Smart Gadget via Bluetooth
        before fetching data from it. The Bluetooth connection will automatically be
        created and destroyed when requesting information from the Smart Gadget if the
        Bluetooth connection does not already exist.

        Establishing a Bluetooth connection to a Smart Gadget takes approximately 7 seconds.
        If you are only requesting data from a couple of Smart Gadgets then connecting to each
        Smart Gadget at the beginning of your script and then fetching data in a loop would
        be more efficient if you want to fetch data as fast as possible (`fast` is used very
        loosely here since it takes approximately 1.5 seconds to read data from a Smart Gadget
        even if the Raspberry Pi already has a Bluetooth connection to it). However, there are
        hardware limits to how many Smart Gadgets can simultaneously have a Bluetooth connection
        with the Raspberry Pi. So, there is a compromise between how `fast` your program can
        fetch data and how many Smart Gadgets you want to fetch data from.

        :param str mac_address: The MAC address of the Smart Gadget to connect to.
        :param bool strict: Whether to raise an error if the Smart Gadget could not be connected to.
        :return: Whether the connection was successful.
        :rtype: bool
        """
        failed = self.connect_gadgets([mac_address], strict=strict)[1]
        return len(failed) == 0

    def connect_gadgets(self, mac_addresses, strict=True) -> Tuple[list, list]:
        """Connect to the specified Smart Gadgets.

        It is not necessary to call this method to connect to a Smart Gadget via Bluetooth
        before fetching data from it. The Bluetooth connection will automatically be
        created and destroyed when requesting information from the Smart Gadget if the
        Bluetooth connection does not already exist.

        Establishing a Bluetooth connection to a Smart Gadget takes approximately 7 seconds.
        If you are only requesting data from a couple of Smart Gadgets then connecting to each
        Smart Gadget at the beginning of your script and then fetching data in a loop would
        be more efficient if you want to fetch data as fast as possible (`fast` is used very
        loosely here since it takes approximately 1.5 seconds to read data from a Smart Gadget
        even if the Raspberry Pi already has a Bluetooth connection to it). However, there are
        hardware limits to how many Smart Gadgets can simultaneously have a Bluetooth connection
        with the Raspberry Pi. So, there is a compromise between how `fast` your program can
        fetch data and how many Smart Gadgets you want to fetch data from.

        :param list mac_addresses: A list of MAC addresses of the Smart Gadget to connect to.
        :param bool strict: Whether to raise an error if a Smart Gadget could not be connected to.
        :return: A list of MAC addresses of the Smart Gadgets that were successfully connected to
                 and the MAC addresses of the Smart Gadgets that could not be connected to.
        :rtype: tuple of list
        """
        failed_connections = []
        for mac_address in mac_addresses:
            if mac_address in self._gadgets_available:
                try:
                    self._gadgets_connected[mac_address] = self._connect(mac_address)[0]
                except BTLEDisconnectError:
                    if strict:
                        raise
                    else:
                        failed_connections.append(mac_address)
        return list(self._gadgets_connected), failed_connections

    def connected_gadgets(self) -> List[str]:
        """A list of MAC addresses of the Smart Gadgets that are currently connected."""
        return list(self._gadgets_connected)

    def disconnect_gadget(self, mac_address: str):
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

    def temperature(self, mac_address: str) -> float:
        """Returns the temperature [degree C] for the specified MAC address."""
        return self._process('temperature', mac_address)

    def humidity(self, mac_address: str) -> float:
        """Returns the humidity [%RH] for the specified MAC address."""
        return self._process('humidity', mac_address)

    def dewpoint(self, mac_address: str, temperature=None, humidity=None) -> float:
        """Returns the dew point [degree C] for the specified MAC address."""
        return self._process('dewpoint', mac_address, temperature=temperature, humidity=humidity)

    def temperature_humidity(self, mac_address: str) -> List[float]:
        """Returns the temperature [degree C] and humidity [%RH] for the specified MAC address."""
        return self._process('temperature_humidity', mac_address)

    def temperature_humidity_dewpoint(self, mac_address: str) -> Tuple[float, float, float]:
        """Returns the temperature [degree C], humidity [%RH] and dew point [degree C] for the specified MAC address."""
        return self._process('temperature_humidity_dewpoint', mac_address)

    def battery(self, mac_address: str) -> int:
        """Returns the battery level [%] for the specified MAC address."""
        return self._process('battery', mac_address)

    def rssi(self, mac_address: str) -> int:
        """Returns the Received Signal Strength Indication for the last received broadcast from the device.

        This is an integer value measured in dB, where 0 dB is the maximum (theoretical) signal
        strength, and more negative numbers indicate a weaker signal.
        """
        return self._process('rssi', mac_address)

    def info(self, mac_address: str) -> dict:
        """Returns all available information from the Smart Gadget."""
        return self._process('info', mac_address)

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

    @staticmethod
    def rpi_date() -> str:
        """Returns the current date of the Raspberry Pi in ISO 8601 format."""
        return datetime.now().isoformat()

    @staticmethod
    def set_rpi_date(date: str):
        """Set the date of the Raspberry Pi.

        The `date` must be in the ISO 8601 format.

        This is useful if the Raspberry Pi does not have internet access on startup
        to sync with an online NTP server. Does not set the time zone.
        """
        iso = datetime.fromisoformat(date)
        subprocess.run(['sudo', 'date', '-s', iso.strftime('%a %d %b %Y %I:%M:%S %p')], check=True)

    def _connect(self, mac_address, retries_remaining=None):
        """Connect to the Smart Gadget."""
        if retries_remaining is None:
            retries_remaining = int(self._retries)
        if mac_address in self._gadgets_connected:
            gadget = self._gadgets_connected[mac_address]
        else:
            while True:
                try:
                    if mac_address in self._gadgets_available:
                        # then we'll have the rssi value since we have the bluepy.btle.ScanEntry
                        gadget = self.CLS(self._gadgets_available[mac_address])
                    else:
                        gadget = self.CLS(mac_address)
                    break
                except BTLEDisconnectError:
                    if retries_remaining < 1:
                        raise
                    retries_remaining -= 1
        return gadget, retries_remaining

    def _process(self, method_name, mac_address, **kwargs):
        retries_remaining = int(self._retries)
        while True:
            try:
                gadget, retries_remaining = self._connect(mac_address, retries_remaining=retries_remaining)
                return getattr(gadget, method_name)(**kwargs)
            except BrokenPipeError:
                if retries_remaining < 1:
                    raise
                retries_remaining -= 1
