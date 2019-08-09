"""
The SHT3X series Smart Gadget from Sensirion.
"""
from time import perf_counter
from datetime import datetime
from typing import Tuple

try:
    from bluepy.btle import Peripheral, UUID
except ImportError:  # then not on the Raspberry Pi
    Peripheral, UUID = object, lambda u: u

from . import logger, timestamp_to_milliseconds, milliseconds_to_datetime
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
            'mac_address': self.addr,
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
            data = round(datetime.now().timestamp() * 1000)
        else:
            data = timestamp_to_milliseconds(timestamp)
        self._write(self.SYNC_TIME_MS_HANDLE, '<Q', data)

    def fetch_logged_data(self, *, enable_temperature=True, enable_humidity=True,
                          sync=None, oldest=None, newest=None, as_datetime=False) -> Tuple[list, list]:
        """Returns the logged temperature and humidity values.

        The maximum number of temperature and humidity values that can be logged is 15872 (for each).

        It can take approximately 80 seconds to fetch the maximum amount of data that can be saved
        in the internal memory of the Smart Gadget.

        The data is returned as an N x 2 :class:`list`:

        * The first column is the timestamp :math:`\\rightarrow` :class:`int` or :class:`~datetime.datetime`
        * The second column is the value :math:`\\rightarrow` :class:`float` or :data:`None` (if there was
          an error downloading the value, see :meth:`SHT3XService.fetch_logged_data` for more details)

        Parameters
        ----------
        enable_temperature : :class:`bool`, optional
            Whether to download the temperature values.
        enable_humidity : :class:`bool`, optional
            Whether to download the humidity values.
        sync
            Passed to :meth:`.set_sync_time`.
        oldest
            Passed to :meth:`.set_oldest_timestamp`.
        newest
            Passed to :meth:`.set_newest_timestamp`.
        as_datetime : :class:`bool`
            If :data:`True` then return the timestamps as :class:`~datetime.datetime` objects
            otherwise return the timestamps as an :class:`int` in milliseconds.

        Returns
        -------
        :class:`list`
            The logged temperature values [degree C].
        :class:`list`
            The logged humidity values [%RH].
        """
        if not enable_temperature and not enable_humidity:
            return [], []

        # enable notifications
        if enable_temperature:
            self.enable_temperature_notifications()
        if enable_humidity:
            self.enable_humidity_notifications()

        # set the logger timestamp information
        self.set_sync_time(sync)
        self.set_oldest_timestamp(oldest or 0)
        if newest is not None:
            self.set_newest_timestamp(newest)

        # get the actual logger timestamp information
        interval = self.logger_interval()
        oldest = self.oldest_timestamp()
        newest = self.newest_timestamp()

        # download the data
        self.delegate.prepare(interval, oldest, newest, enable_temperature, enable_humidity)
        self._write(self.START_LOGGER_DOWNLOAD_HANDLE, '<B', 1)
        while True:
            self.waitForNotifications(1)
            if self.delegate.temperatures_finished and self.delegate.humidities_finished:
                break
        self._write(self.START_LOGGER_DOWNLOAD_HANDLE, '<B', 0)

        # disable notifications
        if enable_temperature:
            self.disable_temperature_notifications()
        if enable_humidity:
            self.disable_humidity_notifications()

        if as_datetime:
            temperatures = [[milliseconds_to_datetime(ms), v] for ms, v in self.delegate.temperatures]
            humidities = [[milliseconds_to_datetime(ms), v] for ms, v in self.delegate.humidities]
            return temperatures, humidities

        return self.delegate.temperatures, self.delegate.humidities


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

    def fetch_logged_data(self, mac_address, *, enable_temperature=True, enable_humidity=True, sync=None,
                          oldest=None, newest=None, as_datetime=False, num_iterations=1) -> Tuple[list, list]:
        """Returns the logged temperature and humidity values.

        The maximum number of temperature and humidity values that can be logged is 15872 (for each).

        It can take approximately 80 seconds per iteration to fetch the maximum amount of data that
        can be saved in the internal memory of the Smart Gadget.

        The data is returned as an N x 2 :class:`list`:

        * The first column is the timestamp :math:`\\rightarrow` :class:`int` or :class:`~datetime.datetime`
        * The second column is the value :math:`\\rightarrow` :class:`float` or :data:`None` (if there was
          an error downloading the value)

        Parameters
        ----------
        mac_address : :class:`str`
            The MAC address of the Smart Gadget.
        enable_temperature : :class:`bool`, optional
            Whether to download the temperature values.
        enable_humidity : :class:`bool`, optional
            Whether to download the humidity values.
        sync
            Passed to :meth:`.SHT3X.set_sync_time`.
        oldest
            Passed to :meth:`.SHT3X.set_oldest_timestamp`.
        newest
            Passed to :meth:`.SHT3X.set_newest_timestamp`.
        as_datetime : :class:`bool`
            If :data:`True` then return the timestamps as :class:`~datetime.datetime` objects
            otherwise return the timestamps as an :class:`int` in milliseconds. If you are
            calling this method from a remote computer (i.e., you are not running your script
            on a Raspberry Pi) then you **must** keep this value as :data:`False` otherwise
            you will get the following error:

              ``TypeError: Object of type datetime is not JSON serializable``

            You can convert the timestamps after getting the data from the Raspberry Pi
            by calling :func:`~smartgadget.milliseconds_to_datetime` on each timestamp.
        num_iterations : :class:`int`, optional
            Bluetooth does not guarantee that all data packets are received by default, its
            connection principles are equivalent to the same ones as UDP for computer networks.
            You can specify the number of times to download the data to fix missing packets.

        Returns
        -------
        :class:`list`
            The logged temperature values [degree C].
        :class:`list`
            The logged humidity values [%RH].
        """
        def bad_timestamps(array):
            # Get the timestamps that contain values that are `None`
            return [ms for ms, v in array if v is None]

        def merge(logger_interval, original, latest):
            # Merge the data from `latest` into `original` that isn't `None`
            if not latest:
                return

            # Cannot compare the timestamps to merge the two lists because the timestamps
            # have too much variability based on syncing with an external clock. Compare
            # the values instead.
            #
            # Find the index offset such that the values in the 2 lists are exactly the
            # same (element wise).
            index = max(0, round(abs(latest[0][0] - original[0][0]) / logger_interval) - 1)
            # check a range of indices centered around the best-guess index
            indices = [index, index - 1, index + 1, index - 2, index + 2]
            n1, n2 = len(original), len(latest)
            for i in indices:
                if i < 0:
                    continue
                index, j = i, 0
                while i < n1 and j < n2:
                    v1, v2 = original[i][1], latest[j][1]
                    if v1 is not None and v2 is not None and v1 != v2:
                        # then we have not found the index that aligns the 2 lists
                        # as long as this index isn't the last item in the `indices`
                        # list then we will try the next item in the `indices` list
                        assert index != indices[-1], 'merging value mismatch -> {} != {}'.format(v1, v2)
                        break
                    i += 1
                    j += 1
                break  # all values that are not `None` are exactly the same (element-wise)

            # we now have the index that aligns the lists, so merge them
            i, j = index, 0
            n1, n2 = len(original), len(latest)
            while i < n1 and j < n2:
                row = original[i]
                value = latest[j][1]
                if value is not None:
                    row[1] = value
                i += 1
                j += 1

        delegate = self._gadgets_connected[mac_address].delegate
        interval = delegate.interval
        temperatures, humidities = [], []
        for iteration in range(num_iterations):

            if not enable_temperature and not enable_humidity:
                break

            t0 = perf_counter()
            latest_t, latest_h = self._process(
                'fetch_logged_data', mac_address,
                enable_temperature=enable_temperature, enable_humidity=enable_humidity,
                sync=sync, oldest=oldest, newest=newest, as_datetime=False
            )
            dt = perf_counter() - t0

            if iteration == 0:
                temperatures, humidities = latest_t, latest_h
            else:
                merge(interval, temperatures, latest_t)
                merge(interval, humidities, latest_h)

            # has all the data been downloaded?
            bad_timestamps_t = bad_timestamps(temperatures)
            bad_timestamps_h = bad_timestamps(humidities)
            if not bad_timestamps_t and not bad_timestamps_h:
                break

            enable_temperature = len(bad_timestamps_t) > 0
            enable_humidity = len(bad_timestamps_h) > 0

            # There is no point trying to re-download data from the Smart Gadget for the
            # values that are still `None` if the data is no longer available in the internal
            # memory of the Smart Gadget
            if enable_temperature:
                enable_temperature = bad_timestamps_t[-1] > latest_t[0][0]
            if enable_humidity:
                enable_humidity = bad_timestamps_h[-1] > latest_h[0][0]

            if latest_t:
                n = len(latest_t) - len(bad_timestamps(latest_t))
                logger.debug('Iteration {} of {} -- Fetched {} of {} temperature values in {:.3f} seconds. '
                             '{} values are still missing'
                             .format(iteration+1, num_iterations, n, len(latest_t), dt, len(bad_timestamps_t)))
            if latest_h:
                n = len(latest_h) - len(bad_timestamps(latest_h))
                logger.debug('Iteration {} of {} -- Fetched {} of {} humidity values in {:.3f} seconds. '
                             '{} values are still missing'
                             .format(iteration+1, num_iterations, n, len(latest_h), dt, len(bad_timestamps_h)))

            # Only fetch data in the range that still contains `None` values.
            # Extend the range a little bit.
            #
            # One could modify the values of 'oldest' and 'newest' more cleverly to only
            # re-download the data where the values are still 'None' in smaller ranges.
            # However, there is a large overhead in setting up the Smart Gadget when
            # 'fetch_logged_data' is called. For example, downloading about 12000 temperature
            # and 12000 humidity data points takes about 80 seconds, so 24000/80 = 300 values/second.
            # If, for example, one specified a timestamp range that fetched 9 temperature and 9
            # humidity values then that took about 1.5 seconds, so 18/1.5 = 12 values/second.
            # Since the missing data packets are randomly scattered in small (4-, 8-, 12-byte)
            # chunks throughout the data there is really no point trying to re-download small
            # time ranges.
            #
            # TODO Once the ranges where the data values need to be re-downloaded become isolated
            #  clusters, like 20 missing values within the first 100 data points and 4 missing
            #  values within the last 100 data points, we could start to break up fetching
            #  the data into smaller ranges
            oldest_t = bad_timestamps_t[0] if bad_timestamps_t else delegate.oldest
            oldest_h = bad_timestamps_h[0] if bad_timestamps_h else delegate.oldest
            oldest = min(oldest_t, oldest_h) - 2 * interval
            newest_t = bad_timestamps_t[-1] if bad_timestamps_t else delegate.newest
            newest_h = bad_timestamps_h[-1] if bad_timestamps_h else delegate.newest
            newest = max(newest_t, newest_h) + 2 * interval

        if temperatures:
            n = len(temperatures) - len(bad_timestamps(temperatures))
            logger.debug('Finished -- Fetched {} of {} temperature values'.format(n, len(temperatures)))

        if humidities:
            n = len(humidities) - len(bad_timestamps(humidities))
            logger.debug('Finished -- Fetched {} of {} humidity values'.format(n, len(humidities)))

        if as_datetime:
            t = [[milliseconds_to_datetime(ms), v] for ms, v in temperatures]
            h = [[milliseconds_to_datetime(ms), v] for ms, v in humidities]
            return t, h

        return temperatures, humidities
