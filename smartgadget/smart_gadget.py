"""
Base class for a Smart Gadget.
"""
import struct
from datetime import datetime
from typing import Union, Tuple

try:
    from bluepy.btle import Peripheral, DefaultDelegate, UUID
except ImportError:  # then not on the Raspberry Pi
    Peripheral, DefaultDelegate, UUID = object, object, lambda u: u

from . import dewpoint


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
            return values[0]
        return values

    def _write(self, hnd_or_uuid, fmt, value, with_response=False):
        """Write a value.

        hnd_or_uuid: A handle (int) or uuid (str)
        fmt (str): The format to pass to struct.pack()
        value: The value to write
        """
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
        self.initialize(-1, 0, 0, True, True)
        self.run_number_offset = 1  # the manual says it starts at 0 but it actually starts at 1 (for firmware v1.3)
        self.max_run_number_repeats = 5

    def initialize(self, logger_interval, oldest_timestamp, newest_timestamp, enable_temperature, enable_humidity):
        """Automatically called before getting the notifications to initialize all parameters."""
        self.temperatures = []
        self.humidities = []
        self.temperatures_finished = not enable_temperature
        self.humidities_finished = not enable_humidity
        self.finished = False  # whether all the logged data was downloaded
        self.logger_interval = logger_interval * 1e-3
        self.oldest_timestamp = oldest_timestamp * 1e-3
        self.newest_timestamp = newest_timestamp * 1e-3
        self.previous_temperature_run_number = -1
        self.previous_humidity_run_number = -1
        self.temperature_run_number_repeats = 0  # the number of times the run number did not change
        self.humidity_run_number_repeats = 0  # the number of times the run number did not change

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

            # avoid multiple attribute lookups in the loop
            fromtimestamp = datetime.fromtimestamp
            newest_timestamp = self.newest_timestamp
            logger_interval = self.logger_interval
            if handle == self.parent.TEMPERATURE_HANDLE:
                append = self.temperatures.append
            elif handle == self.parent.HUMIDITY_HANDLE:
                append = self.humidities.append
            else:
                raise ValueError('Unhandled notification from handle={}'.format(handle))

            run_number = values[0] - self.run_number_offset
            for v in values[1:]:
                # converting to an ISO timestamp is typically faster than the time it takes to
                # receive the next notification so this conversion doesn't really slow things down
                append([run_number, str(fromtimestamp(newest_timestamp - run_number * logger_interval)), v])
                run_number += 1

        else:
            # notification for a single temperature or humidity value
            # its possible that a single value is intermittent with the logged notification
            # therefore we must introduce checks to decide if downloading the logged data has finished
            if handle == self.parent.TEMPERATURE_HANDLE:
                if self.temperatures:  # check if all logged data was downloaded
                    run_number = self.temperatures[-1][0] + self.run_number_offset
                    last_timestamp = self.newest_timestamp - run_number * self.logger_interval
                    if last_timestamp <= self.oldest_timestamp or \
                            self.temperature_run_number_repeats > self.max_run_number_repeats:
                        self.temperatures_finished = True
                        self.parent.disable_temperature_notifications()
                    if self.previous_temperature_run_number == run_number:
                        self.temperature_run_number_repeats += 1
                    else:
                        self.temperature_run_number_repeats = 0
                    self.previous_temperature_run_number = run_number
            elif handle == self.parent.HUMIDITY_HANDLE:
                if self.humidities:  # check if all logged data was downloaded
                    run_number = self.humidities[-1][0] + self.run_number_offset
                    last_timestamp = self.newest_timestamp - run_number * self.logger_interval
                    if last_timestamp <= self.oldest_timestamp or \
                            self.humidity_run_number_repeats > self.max_run_number_repeats:
                        self.humidities_finished = True
                        self.parent.disable_humidity_notifications()
                    if self.previous_humidity_run_number == run_number:
                        self.humidity_run_number_repeats += 1
                    else:
                        self.humidity_run_number_repeats = 0
                    self.previous_humidity_run_number = run_number
            else:
                raise ValueError('Unhandled notification from handle={}'.format(handle))

            self.finished = self.temperatures_finished and self.humidities_finished
