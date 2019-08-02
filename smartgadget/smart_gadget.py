"""
Base class for a Smart Gadget.
"""
import struct
from typing import Union, Tuple

try:
    from bluepy.btle import Peripheral, DefaultDelegate, UUID
except ImportError:  # then not on the Raspberry Pi
    Peripheral, DefaultDelegate, UUID = object, object, lambda u: ()

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
        """
        :param device: A MAC address as a :class:`str` or a :class:`~bluepy.btle.ScanEntry` object.
        :param int interface: The Bluetooth interface to use for the connection.
                              For example, 0 or None means ``/dev/hci0``, 1 means ``/dev/hci1``
        """
        super(SmartGadget, self).__init__(deviceAddr=device, addrType='random', iface=interface)
        self._rssi = None if isinstance(device, str) else device.rssi
        self.withDelegate(NotificationHandler(self))
        self._characteristics = {}

    def temperature(self) -> float:
        """Returns the temperature [degree C]"""
        raise NotImplementedError

    def humidity(self) -> float:
        """Returns the humidity [%RH]"""
        raise NotImplementedError

    def temperature_humidity(self) -> Tuple[float, float]:
        """Returns the temperature [degree C] and humidity [%RH]"""
        raise NotImplementedError

    def battery(self) -> int:
        """Returns the battery level [%]"""
        raise NotImplementedError

    def info(self) -> dict:
        """Returns all available information from the Smart Gadget."""
        raise NotImplementedError

    def dewpoint(self, temperature=None, humidity=None) -> float:
        """Returns the dewpoint [degree C].

        If the `temperature` or `humidity` value is not specified
        then it will be read from the Smart Gadget.
        """
        if temperature is None and humidity is None:
            temperature, humidity = self.temperature_humidity()
        elif temperature is None:
            temperature = self.temperature()
        elif humidity is None:
            humidity = self.humidity()
        return dewpoint(temperature, humidity)

    def temperature_humidity_dewpoint(self) -> Tuple[float, float, float]:
        """Returns the temperature [degree C], humidity [%RH] and dew point [degree C]."""
        t, h = self.temperature_humidity()
        return t, h, self.dewpoint(temperature=t, humidity=h)

    def rssi(self) -> Union[int, None]:
        """Returns the Received Signal Strength Indication for the last received broadcast from the device.

        Only valid if the :class:`SmartGadget` was initialized with a :class:`~bluepy.btle.ScanEntry`
        object, otherwise returns :data:`None`.
        """
        return self._rssi

    def _read(self, hnd_or_uuid, fmt=None):
        """Read data.

        :param hnd_or_uuid: A handle (int) or uuid
        :param fmt: The format to pass to struct.unpack(), if None then assumes an ASCII string.
        :return: The data.
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

        :param hnd_or_uuid: A handle (int) or uuid
        :param fmt: The format to pass to struct.pack()
        :param value: The value to write
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
        super(NotificationHandler, self).__init__()
        self.temperatures = []
        self.humidities = []
        self.finished = False  # whether all the logged data was downloaded
        self.parent = parent

    def initialize(self):
        self.temperatures.clear()
        self.humidities.clear()
        self.finished = False

    def handleNotification(self, handle, data):
        n = (len(data) - 4)//4
        print('notification', n, len(data), data)
        if n > 0:
            values = struct.unpack('<I{}f'.format(n), data)
            print(values)
            if handle == self.parent.TEMPERATURE_HANDLE:
                array = self.temperatures
            else:
                array = self.humidities
            run_number = values[0]
            for v in values[1:]:
                array.append([run_number, v])
                run_number += 1
        #else:
        #    self.finished = True
        #    self.parent.disable_temperature_notifications()
        #    self.parent.disable_humidity_notifications()


