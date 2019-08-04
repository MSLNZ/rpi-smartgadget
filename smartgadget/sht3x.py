"""
The SHT3X series Smart Gadget from Sensirion.
"""
import time
import heapq
from typing import Tuple

try:
    from bluepy.btle import Peripheral, UUID
except ImportError:  # then not on the Raspberry Pi
    Peripheral, UUID = object, lambda u: u

from . import logger, timestamp_to_milliseconds
from .smart_gadget import SmartGadget
from .service import SmartGadgetService


class SHT3X(SmartGadget):

    # This equals the value of DEVICE_NAME_CHARACTERISTIC_UUID
    DEVICE_NAME = 'Smart Humigadget'

    # The following UUID's were taken from
    # https://github.com/Sensirion/SmartGadget-Firmware/blob/master/Simple_BLE_Profile_Description.pdf
    LOGGER_SERVICE_UUID = UUID('0000f234-b38d-4985-720e-0f993a68ee41')
    SYNC_TIME_MS_CHARACTERISTIC_UUID = UUID('0000f235-b38d-4985-720e-0f993a68ee41')
    OLDEST_TIMESTAMP_MS_CHARACTERISTIC_UUID = UUID('0000f236-b38d-4985-720e-0f993a68ee41')
    NEWEST_TIMESTAMP_MS_CHARACTERISTIC_UUID = UUID('0000f237-b38d-4985-720e-0f993a68ee41')
    START_LOGGER_DOWNLOAD_CHARACTERISTIC_UUID = UUID('0000f238-b38d-4985-720e-0f993a68ee41')
    LOGGER_INTERVAL_MS_CHARACTERISTIC_UUID = UUID('0000f239-b38d-4985-720e-0f993a68ee41')
    HUMIDITY_SERVICE_UUID = UUID('00001234-b38d-4985-720e-0f993a68ee41')
    HUMIDITY_CHARACTERISTIC_UUID = UUID('00001235-b38d-4985-720e-0f993a68ee41')
    TEMPERATURE_SERVICE_UUID = UUID('00002234-b38d-4985-720e-0f993a68ee41')
    TEMPERATURE_CHARACTERISTIC_UUID = UUID('00002235-b38d-4985-720e-0f993a68ee41')

    # The following HANDLE's were determined manually for each UUID above.
    # The firmware version number of the Smart Gadget was 1.3
    #
    # Reading the value using the HANDLE is about 14x faster than reading from the UUID.
    # However, this speed-up is only true the initial time that the value is requested.
    # If one creates a Characteristic object from a UUID the object caches the HANDLE
    # for future read/write calls.
    #
    # For example:
    # p = Peripheral(deviceAddr=MAC_ADDRESS, addrType='random')
    # value = p.readCharacteristic(HANDLE)   <-- 14x faster than the following 2 lines
    # c = p.getCharacteristics(uuid=UUID)[0] <-- creating the Characteristic object is the time-consuming part
    # value = c.read()                       <-- this is equivalent to passing the HANDLE

    DEVICE_NAME_HANDLE = 0x03  # READ
    APPEARANCE_HANDLE = 0x05  # READ
    PERIPHERAL_PREFERRED_CONNECTION_PARAMETERS_HANDLE = 0x07  # READ
    MANUFACTURER_NAME_STRING_HANDLE = 0x10  # READ
    SYSTEM_ID_HANDLE = 0x0e  # READ
    MODEL_NUMBER_STRING_HANDLE = 0x12  # READ
    SERIAL_NUMBER_STRING_HANDLE = 0x14  # READ
    HARDWARE_REVISION_STRING_HANDLE = 0x16  # READ
    FIRMWARE_REVISION_STRING_HANDLE = 0x18  # READ
    SOFTWARE_REVISION_STRING_HANDLE = 0x1a  # READ
    BATTERY_LEVEL_HANDLE = 0x1d  # READ

    SYNC_TIME_MS_HANDLE = 0x21  # WRITE
    OLDEST_TIMESTAMP_MS_HANDLE = 0x24  # READ + WRITE
    NEWEST_TIMESTAMP_MS_HANDLE = 0x27  # READ + WRITE
    START_LOGGER_DOWNLOAD_HANDLE = 0x2a  # WRITE
    LOGGER_INTERVAL_MS_HANDLE = 0x2e  # READ + WRITE
    HUMIDITY_HANDLE = 0x32  # READ
    HUMIDITY_NOTIFICATION_HANDLE = 0x34  # READ + WRITE
    TEMPERATURE_HANDLE = 0x37  # READ
    TEMPERATURE_NOTIFICATION_HANDLE = 0x39  # READ + WRITE

    def temperature(self) -> float:
        """Returns the current temperature.

        Returns
        -------
        :class:`float`
            The current temperature [degree C].
        """
        return self._read(self.TEMPERATURE_HANDLE, '<f')

    def humidity(self) -> float:
        """Returns the current humidity.

        Returns
        -------
        :class:`float`
            The current humidity [%RH].
        """
        return self._read(self.HUMIDITY_HANDLE, '<f')

    def temperature_humidity(self) -> Tuple[float, float]:
        """Returns the current temperature and humidity.

        Returns
        -------
        :class:`float`
            The current temperature [degree C].
        :class:`float`
            The current humidity [%RH].
        """
        return self.temperature(), self.humidity()

    def battery(self) -> int:
        """Returns the battery level.

        Returns
        -------
        :class:`float`
            The current battery level [%].
        """
        return self._read(self.BATTERY_LEVEL_HANDLE, '<B')

    def info(self) -> dict:
        """Returns all available information from the Smart Gadget.

        Returns
        -------
        :class:`dict`
            Includes information such as the firmware, hardware and software version numbers,
            the battery level, the temperature, humidity and dew point values and the timing
            information about the data logger.
        """
        # ignore Appearance and Peripheral Preferred Connection Parameters since they are not relevant
        t, h = self.temperature_humidity()
        return {
            'battery': self.battery(),
            'device_name': self.DEVICE_NAME,
            'dewpoint': self.dewpoint(temperature=t, humidity=h),
            'firmware_revision': self._read(self.FIRMWARE_REVISION_STRING_HANDLE),
            'hardware_revision': self._read(self.HARDWARE_REVISION_STRING_HANDLE),
            'humidity': h,
            'logger_interval_ms': self.logger_interval(),
            'manufacturer': self._read(self.MANUFACTURER_NAME_STRING_HANDLE),
            'model_number': self._read(self.MODEL_NUMBER_STRING_HANDLE),
            'newest_timestamp_ms': self.newest_timestamp(),
            'oldest_timestamp_ms': self.oldest_timestamp(),
            'rssi': self.rssi(),
            'serial_number': self._read(self.SERIAL_NUMBER_STRING_HANDLE),
            'software_revision': self._read(self.SOFTWARE_REVISION_STRING_HANDLE),
            'system_id': self._read(self.SYSTEM_ID_HANDLE, '<Q'),
            'temperature': t,
        }

    def oldest_timestamp(self) -> int:
        """Returns the oldest timestamp of the data logger.

        Returns
        -------
        :class:`int`
            The oldest timestamp [milliseconds].  See also :func:`~smartgadget.milliseconds_to_datetime`.
        """
        return self._read(self.OLDEST_TIMESTAMP_MS_HANDLE, '<Q')

    def set_oldest_timestamp(self, timestamp):
        """Set the oldest timestamp of the data logger.

        Parameters
        ----------
        timestamp
            Can be a :class:`~datetime.datetime` object, an ISO-8601 formatted
            :class:`str`, a :class:`float` in seconds, or an :class:`int` in milliseconds.
        """
        self._write(self.OLDEST_TIMESTAMP_MS_HANDLE, '<Q', timestamp_to_milliseconds(timestamp))

    def newest_timestamp(self) -> int:
        """Returns the newest timestamp of the data logger.

        Returns
        -------
        :class:`int`
            The newest timestamp [milliseconds]. See also :func:`~smartgadget.milliseconds_to_datetime`.
        """
        return self._read(self.NEWEST_TIMESTAMP_MS_HANDLE, '<Q')

    def set_newest_timestamp(self, timestamp):
        """Set the newest timestamp of the data logger.

        Parameters
        ----------
        timestamp
            Can be a :class:`~datetime.datetime` object, an ISO-8601 formatted
            :class:`str`, a :class:`float` in seconds, or an :class:`int` in milliseconds.
        """
        self._write(self.NEWEST_TIMESTAMP_MS_HANDLE, '<Q', timestamp_to_milliseconds(timestamp))

    def logger_interval(self) -> int:
        """Returns the data logger interval.

        Returns
        -------
        :class:`int`
            The time between log events [milliseconds].
        """
        return self._read(self.LOGGER_INTERVAL_MS_HANDLE, '<L')

    def set_logger_interval(self, milliseconds):
        """Set the data logger interval.

        .. attention::

           This will clear all values that are currently saved in memory.

        Parameters
        ----------
        milliseconds : :class:`int`
            The time between log events [milliseconds].
        """
        self._write(self.LOGGER_INTERVAL_MS_HANDLE, '<L', int(milliseconds))

    def temperature_notifications_enabled(self) -> bool:
        """Returns whether temperature notifications are enabled.

        Returns
        -------
        :class:`bool`
            Whether temperature notifications are enabled.
        """
        return bool(self._read(self.TEMPERATURE_NOTIFICATION_HANDLE, '<H'))

    def enable_temperature_notifications(self):
        """Enable temperature notifications."""
        self._write(self.TEMPERATURE_NOTIFICATION_HANDLE, '<H', 1)

    def disable_temperature_notifications(self):
        """Disable temperature notifications."""
        self._write(self.TEMPERATURE_NOTIFICATION_HANDLE, '<H', 0)

    def humidity_notifications_enabled(self) -> bool:
        """Returns whether humidity notifications are enabled.

        Returns
        -------
        :class:`bool`
            Whether humidity notifications are enabled.
        """
        return bool(self._read(self.HUMIDITY_NOTIFICATION_HANDLE, '<H'))

    def enable_humidity_notifications(self):
        """Enable humidity notifications."""
        self._write(self.HUMIDITY_NOTIFICATION_HANDLE, '<H', 1)

    def disable_humidity_notifications(self):
        """Disable humidity notifications."""
        self._write(self.HUMIDITY_NOTIFICATION_HANDLE, '<H', 0)

    def set_sync_time(self, timestamp=None):
        """Sync the timestamps of the data logger.

        Parameters
        ----------
        timestamp
            Can be a :class:`~datetime.datetime` object, an ISO-8601 formatted
            :class:`str`, a :class:`float` in seconds, or an :class:`int` in milliseconds.
            If :data:`None` then uses the current time of the Raspberry Pi.
        """
        if timestamp is None:
            data = round(time.time() * 1000)
        else:
            data = timestamp_to_milliseconds(timestamp)
        self._write(self.SYNC_TIME_MS_HANDLE, '<Q', data)

    def fetch_logged_data(self, enable_temperature=True, enable_humidity=True, num_iterations=1,
                          sync=None, oldest=None, newest=None) -> Tuple[list, list]:
        """Returns the logged temperature and humidity values.

        The maximum number of temperature values that can be logged is 15872 and
        the maximum number of humidity values that can be logged is 15872.

        It can take approximately 1 minute to perform 1 iteration of the
        download if the Smart Gadget memory is full and you are requesting all data.

        The data is returned as an N x 3 :class:`list`:

        * the first column is the run number (as documented in the manual) :math:`\\rightarrow` :class:`int`
        * the second column is the timestamp (in ISO-8601 format) :math:`\\rightarrow` :class:`str`
        * the third column is the value :math:`\\rightarrow` :class:`float`

        Parameters
        ----------
        enable_temperature : :class:`bool`, optional
            Whether to download the temperature values.
        enable_humidity : :class:`bool`, optional
            Whether to download the humidity values.
        num_iterations : :class:`int`, optional
            Bluetooth does not guarantee that all data packets are received by default, its
            connection principles are equivalent to the same ones as UDP for computer networks.
            You can specify the number of times to download the data to fix missing packets.
        sync
            Passed to :meth:`.set_sync_time`.
        oldest
            Passed to :meth:`.set_oldest_timestamp`.
        newest
            Passed to :meth:`.set_newest_timestamp`.

        Returns
        -------
        :class:`list` of :class:`list`
            The logged temperature values [degree C].
        :class:`list` of :class:`list`
            The logged humidity values [%RH].
        """
        if not enable_temperature and not enable_humidity:
            logger.debug('Chose not to fetch the temperature nor the humidity values')
            return [], []

        # set the logger timestamps
        self.set_sync_time(sync)
        self.set_oldest_timestamp(oldest)
        if newest is not None:
            self.set_newest_timestamp(newest)

        # wait for the values of the oldest and newest timestamps to be updated
        oldest, newest = 0, 0
        while oldest == 0 or newest == 0:
            oldest, newest = self.oldest_timestamp(), self.newest_timestamp()

        interval = self.logger_interval()
        num_expected = (newest - oldest) // interval
        temperatures, humidities = [], []
        for iteration in range(num_iterations):

            if enable_temperature:
                self.enable_temperature_notifications()
            if enable_humidity:
                self.enable_humidity_notifications()

            # start downloading
            self.delegate.initialize(interval, oldest, newest, enable_temperature, enable_humidity)
            self._write(self.START_LOGGER_DOWNLOAD_HANDLE, '<B', 1)
            while True:
                self.waitForNotifications(1)
                if self.delegate.finished:
                    break
            self._write(self.START_LOGGER_DOWNLOAD_HANDLE, '<B', 0)

            if enable_temperature:
                logger.debug('Iteration {} of {} -- Fetched {} of {} temperature values'
                             .format(iteration+1, num_iterations, len(self.delegate.temperatures), num_expected))
            if enable_humidity:
                logger.debug('Iteration {} of {} -- Fetched {} of {} humidity values'
                             .format(iteration+1, num_iterations, len(self.delegate.humidities), num_expected))

            if num_iterations == 1:
                if enable_temperature:
                    temperatures = self.delegate.temperatures
                if enable_humidity:
                    humidities = self.delegate.humidities
            else:
                def merge_no_duplicates(*iterables):
                    last = object()
                    for val in heapq.merge(*iterables):
                        if val != last:
                            last = val
                            yield val

                # merge the previous and current downloads
                if enable_temperature:
                    temperatures = list(merge_no_duplicates(temperatures, self.delegate.temperatures))
                if enable_humidity:
                    humidities = list(merge_no_duplicates(humidities, self.delegate.humidities))

            # has all the data been downloaded?
            if enable_temperature and len(temperatures) == num_expected and \
                    enable_humidity and len(humidities) == num_expected:
                break
            if not enable_temperature and enable_humidity and len(humidities) == num_expected:
                break
            if not enable_humidity and enable_temperature and len(temperatures) == num_expected:
                break

        if enable_temperature:
            logger.debug('Finished -- Fetched {} of {} temperature values'.format(len(temperatures), num_expected))
        if enable_humidity:
            logger.debug('Finished -- Fetched {} of {} humidity values'.format(len(humidities), num_expected))

        return temperatures, humidities


class SHT3XService(SmartGadgetService):

    def __init__(self, interface=None):
        """The :class:`~msl.network.service.Service` for a :class:`.SHT3X` Smart Gadget.

        Parameters
        ----------
        interface : :class:`int`, optional
            The Bluetooth interface to use for the connection. For example, 0 or :data:`None`
            means ``/dev/hci0``, 1 means ``/dev/hci1``.
        """
        super(SHT3XService, self).__init__(SHT3X, interface=interface)

    def oldest_timestamp(self, mac_address) -> int:
        """Returns the oldest timestamp of the data logger.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`int`
            The oldest timestamp [milliseconds]. See also :func:`~smartgadget.milliseconds_to_datetime`.
        """
        return self._process('oldest_timestamp', mac_address)

    def set_oldest_timestamp(self, mac_address, timestamp):
        """Set the oldest timestamp of the data logger.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        timestamp
            Can be a :class:`~datetime.datetime` object, an ISO-8601 formatted
            :class:`str`, a :class:`float` in seconds, or an :class:`int` in milliseconds.
        """
        self._process('set_oldest_timestamp', mac_address, timestamp=timestamp)

    def newest_timestamp(self, mac_address) -> int:
        """Returns the newest timestamp of the data logger.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`int`
            The newest timestamp [milliseconds]. See also :func:`~smartgadget.milliseconds_to_datetime`.
        """
        return self._process('newest_timestamp', mac_address)

    def set_newest_timestamp(self, mac_address, timestamp):
        """Set the newest timestamp of the data logger.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        timestamp
            Can be a :class:`~datetime.datetime` object, an ISO-8601 formatted
            :class:`str`, a :class:`float` in seconds, or an :class:`int` in milliseconds.
        """
        self._process('set_newest_timestamp', mac_address, timestamp=timestamp)

    def logger_interval(self, mac_address) -> int:
        """Returns the data logger interval.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`int`
            The time between log events [milliseconds].
        """
        return self._process('logger_interval', mac_address)

    def set_logger_interval(self, mac_address, milliseconds):
        """Set the data logger interval.

        .. attention::

           This will clear all values that are currently saved in memory.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        milliseconds : :class:`int`
            The time between log events [milliseconds].
        """
        self._process('set_logger_interval', mac_address, milliseconds=milliseconds)

    def temperature_notifications_enabled(self, mac_address) -> bool:
        """Returns whether temperature notifications are enabled.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`bool`
            Whether temperature notifications are enabled.
        """
        return self._process('temperature_notifications_enabled', mac_address)

    def enable_temperature_notifications(self, mac_address):
        """Enable temperature notifications.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        """
        self._process('enable_temperature_notifications', mac_address)

    def disable_temperature_notifications(self, mac_address):
        """Disable temperature notifications.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        """
        self._process('disable_temperature_notifications', mac_address)

    def humidity_notifications_enabled(self, mac_address) -> bool:
        """Returns whether humidity notifications are enabled.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.

        Returns
        -------
        :class:`bool`
            Whether humidity notifications are enabled.
        """
        return self._process('humidity_notifications_enabled', mac_address)

    def enable_humidity_notifications(self, mac_address):
        """Enable humidity notifications.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        """
        self._process('enable_humidity_notifications', mac_address)

    def disable_humidity_notifications(self, mac_address):
        """Disable humidity notifications.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        """
        self._process('disable_humidity_notifications', mac_address)

    def set_sync_time(self, mac_address, timestamp=None):
        """Sync the timestamps of the data logger.

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        timestamp
            Can be a :class:`~datetime.datetime` object, an ISO-8601 formatted
            :class:`str`, a :class:`float` in seconds, or an :class:`int` in milliseconds.
            If :data:`None` then uses the current time of the Raspberry Pi.
        """
        self._process('set_sync_time', mac_address, timestamp=timestamp)

    def fetch_logged_data(self, mac_address, enable_temperature=True, enable_humidity=True, num_iterations=1,
                          sync=None, oldest=None, newest=None) -> Tuple[list, list]:
        """Returns the logged temperature and humidity values.

        The maximum number of temperature values that can be logged is 15872 and
        the maximum number of humidity values that can be logged is 15872.

        It can take approximately 1 minute to perform 1 iteration of the
        download if the Smart Gadget memory is full and you are requesting all data.

        The data is returned as an N x 3 :class:`list`:

        * the first column is the run number (as documented in the manual) :math:`\\rightarrow` :class:`int`
        * the second column is the timestamp (in ISO-8601 format) :math:`\\rightarrow` :class:`str`
        * the third column is the value :math:`\\rightarrow` :class:`float`

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        enable_temperature : :class:`bool`, optional
            Whether to download the temperature values.
        enable_humidity : :class:`bool`, optional
            Whether to download the humidity values.
        num_iterations : :class:`int`, optional
            Bluetooth does not guarantee that all data packets are received by default, its
            connection principles are equivalent to the same ones as UDP for computer networks.
            You can specify the number of times to download the data to fix missing packets.
        sync
            Passed to :meth:`.SHT3X.set_sync_time`.
        oldest
            Passed to :meth:`.SHT3X.set_oldest_timestamp`.
        newest
            Passed to :meth:`.SHT3X.set_newest_timestamp`.

        Returns
        -------
        :class:`list` of :class:`list`
            The logged temperature values [degree C].
        :class:`list` of :class:`list`
            The logged humidity values [%RH].
        """
        return self._process('fetch_logged_data', mac_address,
                             enable_temperature=enable_temperature, enable_humidity=enable_humidity,
                             num_iterations=num_iterations, sync=sync, oldest=oldest, newest=newest)
