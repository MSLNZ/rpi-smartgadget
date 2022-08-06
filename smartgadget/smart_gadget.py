"""
Base class for a Smart Gadget.
"""
import struct
from typing import Union, Tuple

try:
    from bluepy.btle import Peripheral, DefaultDelegate, UUID
except ImportError:  # then not on the Raspberry Pi
    Peripheral, DefaultDelegate, UUID = object, object, lambda u: u

from . import dewpoint, logger


class SmartGadget(Peripheral):

    # The following UUID's were taken from
    # https://www.bluetooth.com/specifications/gatt/characteristics/
    # bluepy has these available as AssignedNumbers attributes, but bluepy cannot be pip-installed on Windows
    DEVICE_NAME_CHARACTERISTIC_UUID = UUID(0x2a00)
    APPEARANCE_CHARACTERISTIC_UUID = UUID(0x2a01)
    PERIPHERAL_PREFERRED_CONNECTION_PARAMETERS_CHARACTERISTIC_UUID = UUID(0x2a04)
    BATTERY_LEVEL_CHARACTERISTIC_UUID = UUID(0x2a19)
    SYSTEM_ID_CHARACTERISTIC_UUID = UUID(0x2a23)
    MODEL_NUMBER_STRING_CHARACTERISTIC_UUID = UUID(0x2a24)
    SERIAL_NUMBER_STRING_CHARACTERISTIC_UUID = UUID(0x2a25)
    HARDWARE_REVISION_STRING_CHARACTERISTIC_UUID = UUID(0x2a27)
    FIRMWARE_REVISION_STRING_CHARACTERISTIC_UUID = UUID(0x2a26)
    SOFTWARE_REVISION_STRING_CHARACTERISTIC_UUID = UUID(0x2a28)
    MANUFACTURER_NAME_STRING_CHARACTERISTIC_UUID = UUID(0x2a29)

    def __init__(self, device, interface=None):
        """Base class for a Smart Gadget.

        Parameters
        ----------
        device
            A MAC address as a :class:`str` or a :ref:`ScanEntry <scanentry>` object.
        interface : :class:`int`, optional
            The Bluetooth interface to use for the connection. For example, 0 or :data:`None`
            means ``/dev/hci0``, 1 means ``/dev/hci1``.
        """
        super(SmartGadget, self).__init__(deviceAddr=device, addrType='random', iface=interface)
        self._rssi = None if isinstance(device, str) else device.rssi
        self.withDelegate(NotificationHandler(self))
        self._characteristics = {}

    def __del__(self):
        # suppress all errors from Peripheral, for example, a BrokenPipeError
        try:
            super(SmartGadget, self).__del__()
        except:
            pass

    def temperature(self) -> float:
        """Returns the temperature [degree C].

        .. attention::
           The subclass must override this method.
        """
        raise NotImplementedError

    def humidity(self) -> float:
        """Returns the temperature [degree C].

        .. attention::
           The subclass must override this method.
        """
        raise NotImplementedError

    def temperature_humidity(self) -> Tuple[float, float]:
        """Returns the temperature [degree C].

        .. attention::
           The subclass must override this method.
        """
        raise NotImplementedError

    def battery(self) -> int:
        """Returns the temperature [degree C].

        .. attention::
           The subclass must override this method.
        """
        raise NotImplementedError

    def info(self) -> dict:
        """Returns the temperature [degree C].

        .. attention::
           The subclass must override this method.
        """
        raise NotImplementedError

    def dewpoint(self, temperature=None, humidity=None) -> float:
        """Returns the dew point for the specified MAC address.

        Parameters
        ----------
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
        if temperature is None and humidity is None:
            temperature, humidity = self.temperature_humidity()
        elif temperature is None:
            temperature = self.temperature()
        elif humidity is None:
            humidity = self.humidity()
        return dewpoint(temperature, humidity)

    def temperature_humidity_dewpoint(self) -> Tuple[float, float, float]:
        """Returns the current temperature, humidity and dew point.

        Returns
        -------
        :class:`float`
            The temperature [degree C].
        :class:`float`
            The humidity [%RH].
        :class:`float`
            The dew point [degree C].
        """
        t, h = self.temperature_humidity()
        return t, h, self.dewpoint(temperature=t, humidity=h)

    def rssi(self) -> Union[int, None]:
        """Returns the Received Signal Strength Indication (RSSI) for the last received broadcast from the device.

        This is an integer value measured in dB, where 0 dB is the maximum (theoretical) signal
        strength, and more negative numbers indicate a weaker signal.

        Returns
        -------
        :class:`int` or :data:`None`
            The RSSI value if the :class:`.SmartGadget` was initialized with a
            :ref:`ScanEntry <scanentry>` object. Otherwise returns :data:`None`.
        """
        return self._rssi

    def _read(self, hnd_or_uuid, fmt=None):
        """Read data.

        hnd_or_uuid: A handle (int) or uuid (str)
        fmt (str): The format to pass to struct.unpack(), if None then assumes an ASCII string.
        """
        if isinstance(hnd_or_uuid, int):  # handle
            data = self.readCharacteristic(hnd_or_uuid)
        else:  # uuid
            try:
                c = self._characteristics[hnd_or_uuid]
            except KeyError:
                c = self.getCharacteristics(uuid=hnd_or_uuid)[0]
                self._characteristics[hnd_or_uuid] = c
            data = c.read()
        if fmt is None:
            return data.decode()
        values = struct.unpack(fmt, data)
        if len(values) == 1:
            logger.debug('READ  address=%r characteristic=0x%x -> %s', self.addr, hnd_or_uuid, values[0])
            return values[0]
        logger.debug('READ  address=%r characteristic=0x%x -> %s', self.addr, hnd_or_uuid, values)
        return values

    def _write(self, hnd_or_uuid, fmt, value, with_response=True):
        """Write a value.

        hnd_or_uuid: A handle (int) or uuid (str)
        fmt (str): The format to pass to struct.pack()
        value: The value to write
        """
        logger.debug('WRITE address=%r characteristic=0x%x value=%s', self.addr, hnd_or_uuid, value)
        data = struct.pack(fmt, value)
        if isinstance(hnd_or_uuid, int):  # handle
            self.writeCharacteristic(hnd_or_uuid, data, withResponse=with_response)
        else:  # uuid
            try:
                c = self._characteristics[hnd_or_uuid]
            except KeyError:
                c = self.getCharacteristics(uuid=hnd_or_uuid)[0]
                self._characteristics[hnd_or_uuid] = c
            c.write(data, withResponse=with_response)


class NotificationHandler(DefaultDelegate):

    def __init__(self, parent):
        """Handles notifications from the Smart Gadget.

        Not to be instantiated directly.
        """
        super(NotificationHandler, self).__init__()
        self.parent = parent
        self.temperatures = []
        self.humidities = []
        self.temperatures_finished = False
        self.humidities_finished = False
        self.interval = -1
        self.oldest = -1
        self.newest = -1
        self.temperature_repeats = 0
        self.humidity_repeats = 0
        self.run_number_offset = 1
        self.max_repeats = 5

    def prepare(self, interval, oldest, newest, enable_temperature, enable_humidity):
        """Automatically called before getting the notifications to initialize all parameters."""
        self.temperatures_finished = not enable_temperature
        self.humidities_finished = not enable_humidity
        self.interval = interval
        self.oldest = oldest
        self.newest = newest
        self.temperature_repeats = 0
        self.humidity_repeats = 0

        # the value of the oldest timestamp will never actually downloaded
        # that is why we use range(1, n)
        n = (newest - oldest) // interval + 1
        if enable_temperature:
            self.temperatures = [[oldest + i * interval, None] for i in range(1, n)]
        else:
            self.temperatures = []

        if enable_humidity:
            self.humidities = [[oldest + i * interval, None] for i in range(1, n)]
        else:
            self.humidities = []

    def handleNotification(self, handle, data):
        """Received a notification.

        Parameters
        ----------
        handle : :class:`int`
            The handle that sent the notification.
        data : :class:`bytes`
            The data.
        """
        n = (len(data) - 4)//4
        if n > 0:  # notification for logged data
            values = struct.unpack('<I{}f'.format(n), data)
            if handle == self.parent.TEMPERATURE_HANDLE:
                array = self.temperatures
                self.temperature_repeats = 0
            elif handle == self.parent.HUMIDITY_HANDLE:
                array = self.humidities
                self.humidity_repeats = 0
            else:
                raise ValueError('Unhandled notification from handle={}'.format(handle))

            # data is downloaded from the newest to the oldest log event
            # the manual says that the run number starts at 0 but it actually starts at 1 (for firmware v1.3)
            run_number = values[0] - self.run_number_offset
            index = len(array) - values[0]
            for v in values[1:]:
                row = array[index]
                timestamp = self.newest - run_number * self.interval
                assert row[0] == timestamp, 'timestamp mismatch -> {} != {}'.format(row[0], timestamp)
                row[1] = v
                index -= 1
                run_number += 1

        else:
            # a notification for a single temperature or humidity value
            # it is possible that a single value is received intermittently within the logger notification
            # therefore we must introduce checks to decide if downloading the logged data has finished
            if handle == self.parent.TEMPERATURE_HANDLE:
                if self.temperatures:
                    self.temperatures_finished = self.temperatures[0][1] is not None
                    if not self.temperatures_finished:
                        # then maybe the last data packet never arrived
                        # make sure we don't end up in an infinite loop waiting for packets that will never arrive
                        self.temperature_repeats += 1
                        self.temperatures_finished = self.temperature_repeats >= self.max_repeats
            elif handle == self.parent.HUMIDITY_HANDLE:
                if self.humidities:
                    self.humidities_finished = self.humidities[0][1] is not None
                    if not self.humidities_finished:
                        # then maybe the last data packet never arrived
                        # make sure we don't end up in an infinite loop waiting for packets that will never arrive
                        self.humidity_repeats += 1
                        self.humidities_finished = self.humidity_repeats >= self.max_repeats
            else:
                raise ValueError('Unhandled notification from handle={}'.format(handle))
