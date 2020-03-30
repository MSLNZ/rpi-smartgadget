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

from . import (
    logger,
    timestamp_to_milliseconds,
    milliseconds_to_datetime,
)


class SmartGadgetService(Service):

    def __init__(self, cls, interface=None):
        """Base class for a Smart Gadget :class:`~msl.network.service.Service`.

        Parameters
        ----------
        cls
            A :class:`~smartgadget.sht3x.SHT3XService` or a
            :class:`~smartgadget.shtc1.SHTC1Service` class type.
        interface : :class:`int`, optional
            The Bluetooth interface to use for the connection. For example, 0 or :data:`None`
            means ``/dev/hci0``, 1 means ``/dev/hci1``.
        """
        super(SmartGadgetService, self).__init__(name=cls.DEVICE_NAME)
        self._device_name = cls.DEVICE_NAME
        self._cls = cls
        self._interface = interface
        self._max_attempts = 5
        self._retries_remaining = 0
        self._scanner = Scanner()
        self._gadgets_available = {}
        self._gadgets_connected = {}
        # only add a MAC address in here if the connection request was made explicitly
        self._requested_connections = set()

    def max_attempts(self) -> int:
        """Returns the maximum number of times to try to connect or read/write data from/to a Smart Gadget.

        Returns
        -------
        :class:`int`
            The maximum number of times to retry.
        """
        return self._max_attempts

    def set_max_attempts(self, max_attempts):
        """Set the maximum number of times to try to connect or read/write data from/to a Smart Gadget.

        Since a Bluetooth connection can drop unexpectedly, this provides the opportunity
        to automatically re-connect or re-send a request to a Smart Gadget.

        Parameters
        ----------
        max_attempts : :class:`int`
            The maximum number of times to try to connect or read/write data from/to a Smart Gadget.
            Increasing the number of attempts will decrease the occurrence of getting a
            ``BTLEDisconnectError`` or a :exc:`BrokenPipeError` when sending requests, but may make
            sending a request take a long time while the connection automatically tries to be
            re-established.
        """
        self._max_attempts = max(1, int(max_attempts))
        logger.debug('The maximum number attempts has been set to {}'.format(self._max_attempts))

    def scan(self, timeout=10, passive=False) -> List[str]:
        """Scan for Smart Gadgets that are within Bluetooth range.

        Parameters
        ----------
        timeout : :class:`float`, optional
            The number of seconds to scan for Smart Gadgets.
        passive : :class:`bool`, optional
            Use active (to obtain more information when connecting) or passive scanning.

        Returns
        -------
        :class:`list` of :class:`str`
            A list of MAC addresses of the Smart Gadgets that are available for this
            particular SHTxx class.
        """
        self._gadgets_available.clear()
        logger.info('Scanning for {!r}...'.format(self._device_name))
        for d in self._scanner.scan(timeout=timeout, passive=passive):
            if d.getValueText(d.COMPLETE_LOCAL_NAME) == self._device_name:
                self._gadgets_available[d.addr] = d
        logger.info('Found {} Smart Gadgets'.format(len(self._gadgets_available)))
        return list(self._gadgets_available)

    def connect_gadget(self, mac_address, strict=True) -> bool:
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

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget to connect to.
        strict : :class:`bool`, optional
            Whether to raise an error if the Smart Gadget could not be connected to.

        Returns
        -------
        :class:`bool`
            Whether the connection was successful.
        """
        failed = self.connect_gadgets([mac_address], strict=strict)[1]
        return len(failed) == 0

    def connect_gadgets(self, mac_addresses, strict=True) -> Tuple[list, list]:
        """Connect to the specified Smart Gadgets.

        See :meth:`.connect_gadget` for more details.

        Parameters
        ----------
        mac_addresses : :class:`list` of :class:`str`
            A list of MAC addresses of the Smart Gadgets to connect to.
        strict : :class:`bool`, optional
            Whether to raise an error if a Smart Gadget could not be connected to.

        Returns
        -------
        :class:`tuple` of :class:`list`
            A list of MAC addresses of the Smart Gadgets that were successfully connected to
            and the MAC addresses of the Smart Gadgets that could not be connected to.
        """
        failed_connections = []
        for mac_address in mac_addresses:
            self._retries_remaining = self._max_attempts
            try:
                self._connect(mac_address)
                self._requested_connections.add(mac_address)
            except BTLEDisconnectError as e:
                if strict:
                    logger.error(e)
                    raise
                else:
                    logger.warning('Could not connect to {!r}'.format(mac_address))
                    failed_connections.append(mac_address)
        return list(self._gadgets_connected), failed_connections

    def connected_gadgets(self) -> List[str]:
        """Returns the MAC addresses of the Smart Gadgets that are currently connected.

        Returns
        -------
        :class:`list` of :class:`str`
            The MAC addresses of the currently-connected Smart Gadgets.
        """
        return list(self._gadgets_connected)

    def disconnect_gadget(self, mac_address):
        """Disconnect the Smart Gadget with the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget to disconnect from.
        """
        gadget = self._gadgets_connected.pop(mac_address, None)
        if gadget:
            try:
                logger.info('Disconnecting from {!r}...'.format(mac_address))
                gadget.disconnect()
            except:
                pass
        try:
            self._requested_connections.remove(mac_address)
        except:
            pass

    def disconnect_gadgets(self):
        """Disconnect from all Smart Gadgets."""
        for mac_address, gadget in self._gadgets_connected.items():
            try:
                gadget.disconnect()
            except:
                pass
            try:
                self._requested_connections.remove(mac_address)
            except:
                pass
        self._gadgets_connected.clear()
        logger.info('Disconnected from all Smart Gadgets')

    def temperature(self, mac_address) -> float:
        """Returns the current temperature for the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`float`
            The temperature [degree C].
        """
        return self._process('temperature', mac_address)

    def humidity(self, mac_address) -> float:
        """Returns the current humidity for the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`float`
            The humidity [%RH].
        """
        return self._process('humidity', mac_address)

    def dewpoint(self, mac_address, temperature=None, humidity=None) -> float:
        """Returns the dew point for the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        temperature : :class:`float`, optional
            The temperature [degree C]. If :data:`None` then reads the current
            temperature value from the Smart Gadget.
        humidity : :class:`float`, optional
            The humidity [%RH]. If :data:`None` then reads the current
            humidity value from the Smart Gadget.

        Returns
        -------
        :class:`float`
            The dew point [degree C].
        """
        return self._process('dewpoint', mac_address, temperature=temperature, humidity=humidity)

    def temperature_humidity(self, mac_address) -> Tuple[float, float]:
        """Returns the current temperature and humidity for the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`float`
            The temperature [degree C].
        :class:`float`
            The humidity [%RH].
        """
        return self._process('temperature_humidity', mac_address)

    def temperature_humidity_dewpoint(self, mac_address) -> Tuple[float, float, float]:
        """Returns the current temperature, humidity and dew point for the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`float`
            The temperature [degree C].
        :class:`float`
            The humidity [%RH].
        :class:`float`
            The dew point [degree C].
        """
        return self._process('temperature_humidity_dewpoint', mac_address)

    def battery(self, mac_address) -> int:
        """Returns the battery level for the specified MAC address.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`int`
            The battery level [%].
        """
        return self._process('battery', mac_address)

    def rssi(self, mac_address) -> int:
        """Returns the Received Signal Strength Indication (RSSI) for the last received broadcast from the device.

        This is an integer value measured in dB, where 0 dB is the maximum (theoretical) signal
        strength, and more negative numbers indicate a weaker signal.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`int` or :data:`None`
            The RSSI value if the :class:`~smartgadget.smart_gadget.SmartGadget` was
            initialized with a :ref:`ScanEntry <scanentry>` object. Otherwise returns
            :data:`None`.
        """
        return self._process('rssi', mac_address)

    def info(self, mac_address) -> dict:
        """Returns all available information from the Smart Gadget.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`dict`
            Includes information such as the firmware, hardware and software version numbers,
            the battery level, the temperature, humidity and dew point values and the timing
            information about the data logger (if the Smart Gadgets supports logging).
        """
        return self._process('info', mac_address)

    def shutdown_service(self):
        """Shutdown the Smart Gadget :class:`~msl.network.service.Service` and
        the Network :class:`~msl.network.manager.Manager`."""
        self.disconnect_gadgets()

    def restart_bluetooth(self):
        """Restart the Bluetooth driver on the Raspberry Pi.

        This can fix scanning issues or connection timeouts.

        .. attention::

           Calling this method will disconnect all Smart Gadgets that are currently connected
           to the Raspberry Pi.
        """
        logger.debug('Restarting bluetooth...')
        self.disconnect_gadgets()
        subprocess.run(['sudo', 'systemctl', 'restart', 'bluetooth'], check=True)

    @staticmethod
    def rpi_date() -> str:
        """Returns the current date of the Raspberry Pi.

        Returns
        -------
        :class:`str`
            The current date of the Raspberry Pi in the ISO-8601 format.
        """
        return datetime.now().isoformat(sep=' ')

    @staticmethod
    def set_rpi_date(date):
        """Set the date of the Raspberry Pi.

        This is useful if the Raspberry Pi does not have internet access on startup
        to sync with an online NTP server. Does not set the time zone.

        Parameters
        ----------
        date
            Can be a :class:`~datetime.datetime` object, an ISO-8601
            formatted :class:`str`, a :class:`float` in seconds, or an
            :class:`int` in milliseconds.
        """
        date = milliseconds_to_datetime(timestamp_to_milliseconds(date))
        logger.debug("Setting Raspberry Pi date to '{}'".format(date))
        subprocess.run(['sudo', 'date', '-s', date.strftime('%a %d %b %Y %I:%M:%S %p')], check=True)

    def _connect(self, mac_address):
        """Connect to a Smart Gadget."""
        gadget = self._gadgets_connected.get(mac_address)
        if gadget is None:
            device = self._gadgets_available.get(mac_address) or mac_address
            while gadget is None:
                try:
                    self._retries_remaining -= 1
                    if mac_address in self._requested_connections:
                        logger.info('Re-connecting to {!r}...'.format(mac_address))
                    else:
                        logger.info('Connecting to {!r}...'.format(mac_address))
                    gadget = self._cls(device, interface=self._interface)
                    self._gadgets_connected[mac_address] = gadget
                except BTLEDisconnectError as e:
                    if self._retries_remaining < 1:
                        logger.error(e)
                        raise
                    text = 'retry remains' if self._retries_remaining == 1 else 'retries remaining'
                    logger.warning('{} -- {} {}'.format(e, self._retries_remaining, text))
        return gadget

    def _process(self, method_name, mac_address, **kwargs):
        """All Smart Gadget services call this method to process the request."""
        self._retries_remaining = self._max_attempts
        while True:
            gadget = self._connect(mac_address)
            try:
                logger.info('Processing {!r} from {!r} -- kwargs={}'.format(method_name, mac_address, kwargs))
                out = getattr(gadget, method_name)(**kwargs)
                if mac_address not in self._requested_connections:
                    self.disconnect_gadget(mac_address)
                return out
            except (BrokenPipeError, BTLEDisconnectError) as e:
                if self._retries_remaining < 1:
                    logger.error(e)
                    raise
                self._gadgets_connected.pop(mac_address, None)
                text = 'retry remains' if self._retries_remaining == 1 else 'retries remaining'
                logger.warning('{} -- {} {}'.format(e, self._retries_remaining, text))
