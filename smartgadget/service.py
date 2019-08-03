"""
Base class for a Smart Gadget :class:`~msl.network.service.Service`.
"""
import subprocess
from datetime import datetime
from typing import List, Tuple

from msl.network import Service
try:
    from bluepy.btle import Scanner, BTLEDisconnectError
except ImportError:  # then not on the Raspberry Pi
    Scanner, BTLEDisconnectError = object, object

from . import logger


class SmartGadgetService(Service):

    def __init__(self, cls):
        """Base class for a Smart Gadget :class:`~msl.network.service.Service`.

        :param cls: :class:`~smartgadget.sht3x.SHT3XService` or :class:`~smartgadget.shtc1.SHTC1Service`
        """
        super(SmartGadgetService, self).__init__(name=cls.DEVICE_NAME)
        self.DEVICE_NAME = cls.DEVICE_NAME
        self.CLS = cls
        self._max_attempts = 5
        self._retries_remaining = 0
        self._scanner = Scanner()
        self._gadgets_available = {}
        self._gadgets_connected = {}

    def max_attempts(self) -> int:
        """Returns the maximum number of times to try to connect or read/write data from/to a Smart Gadget.

        Since the Bluetooth connection can drop unexpectedly, this provides the opportunity
        to re-connect or re-send a request to a Smart Gadget.
        """
        return self._max_attempts

    def set_max_attempts(self, value: int):
        """Set the maximum number of times to try to connect or read/write data from/to a Smart Gadget."""
        self._max_attempts = max(1, int(value))
        logger.debug('The maximum number attempts has been set to {}'.format(self._max_attempts))

    def scan(self, timeout=10, passive=False) -> List[str]:
        """Scan for Smart Gadgets that are within Bluetooth range.

        :param float timeout: The number of seconds to scan for Smart Gadgets.
        :param bool passive: Use active (to obtain more information when connecting) or passive scanning.
        :return: A list of MAC addresses of the Smart Gadgets that are available.
        :rtype: list of str
        """
        self._gadgets_available.clear()
        logger.debug('Start scanning for Smart Gadgets...')
        for d in self._scanner.scan(timeout=timeout, passive=passive):
            if d.getValueText(d.COMPLETE_LOCAL_NAME) == self.DEVICE_NAME:
                self._gadgets_available[d.addr] = d
        logger.debug('Found {} Smart Gadgets'.format(len(self._gadgets_available)))
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
        be more efficient if you want to fetch data as quickly as possible. However, there are
        hardware limits to how many Smart Gadgets can simultaneously have a Bluetooth connection
        with the Raspberry Pi. So, there is a compromise between how quickly your program can
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

        See :meth:`.connect_gadget` for more details.

        :param list mac_addresses: A list of MAC addresses of the Smart Gadgets to connect to.
        :param bool strict: Whether to raise an error if a Smart Gadget could not be connected to.
        :return: A list of MAC addresses of the Smart Gadgets that were successfully connected to
                 and the MAC addresses of the Smart Gadgets that could not be connected to.
        :rtype: tuple of list
        """
        failed_connections = []
        for mac_address in mac_addresses:
            self._retries_remaining = self._max_attempts
            try:
                self._gadgets_connected[mac_address] = self._connect(mac_address)
            except BTLEDisconnectError as e:
                if strict:
                    logger.error(e)
                    raise
                else:
                    logger.warning('Could not connect to {!r}'.format(mac_address))
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
                logger.debug('Disconnecting from {!r}...'.format(mac_address))
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
        logger.debug('Disconnected from all Smart Gadgets')

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
        logger.debug('Restarting bluetooth...')
        self.disconnect_gadgets()
        subprocess.run(['sudo', 'systemctl', 'restart', 'bluetooth'], check=True)

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
        logger.debug('Setting Raspberry Pi date to {}'.format(iso))
        subprocess.run(['sudo', 'date', '-s', iso.strftime('%a %d %b %Y %I:%M:%S %p')], check=True)

    def _connect(self, mac_address):
        """Connect to a Smart Gadget."""
        gadget = self._gadgets_connected.get(mac_address)
        if gadget is None:
            device = self._gadgets_available.get(mac_address) or mac_address
            while gadget is None:
                try:
                    self._retries_remaining -= 1
                    logger.debug('Connecting to {!r}...'.format(mac_address))
                    gadget = self.CLS(device)
                except BTLEDisconnectError as e:
                    if self._retries_remaining < 1:
                        logger.error(e)
                        raise
                    text = 'retry remains' if self._retries_remaining == 1 else 'retries remaining'
                    logger.warning('{} -- {} {}'.format(e, self._retries_remaining, text))
        return gadget

    def _process(self, method_name, mac_address, **kwargs):
        logger.debug('Processing {!r} from {!r} -- kwargs={}'.format(method_name, mac_address, kwargs))
        self._retries_remaining = self._max_attempts
        add_to_gadgets_connected = False
        while True:
            gadget = self._connect(mac_address)
            if add_to_gadgets_connected:
                self._gadgets_connected[mac_address] = gadget
                logger.info('MAC address {!r} has been reconnected'.format(mac_address))

            try:
                return getattr(gadget, method_name)(**kwargs)
            except (BrokenPipeError, BTLEDisconnectError) as e:
                if self._retries_remaining < 1:
                    logger.error(e)
                    raise
                add_to_gadgets_connected = self._gadgets_connected.pop(mac_address, None) is not None
                text = 'retry remains' if self._retries_remaining == 1 else 'retries remaining'
                logger.warning('{} -- {} {}'.format(e, self._retries_remaining, text))
