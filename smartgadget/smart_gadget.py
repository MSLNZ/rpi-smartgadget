import struct

try:
    from bluepy.btle import Peripheral, UUID, AssignedNumbers
except ImportError:
    Peripheral = object  # not on the Raspberry Pi
    UUID = lambda u: None


class SmartGadget(Peripheral):

    def __init__(self, scan_entry):
        """:param scan_entry: A bluepy.btle.ScanEntry object."""
        super(SmartGadget, self).__init__(deviceAddr=scan_entry)
        self._scan_entry = scan_entry

    @staticmethod
    def create(scan_entry):
        """:param scan_entry: A bluepy.btle.ScanEntry object."""
        name = scan_entry.getValueText(scan_entry.COMPLETE_LOCAL_NAME)
        if name == SHT3X.NAME:
            return SHT3X(scan_entry)
        elif name == SHTC1.NAME:
            return SHTC1(scan_entry)
        else:
            return None

    def temperature(self):
        """float: the temperature [deg C]"""
        raise NotImplementedError()

    def humidity(self):
        """float: the humidity [%RH]"""
        raise NotImplementedError()

    def dewpoint(self, temperature=None, humidity=None):
        """float: the dew point [deg C]"""
        if temperature is None and humidity is None:
            temperature, humidity = self.temperature_humidity()
        if temperature is None:
            temperature = self.temperature()
        if humidity is None:
            humidity = self.humidity()

        dew = None  # TODO calculation
        return dew

    def temperature_humidity(self):
        """float, float: the temperature [deg C] and humidity [%RH]"""
        raise NotImplementedError()

    def temperature_humidity_dewpoint(self):
        """float, float, float: the temperature [deg C], humidity [%RH] and dew point [deg C]"""
        t, h = self.temperature_humidity()
        return t, h, self.dewpoint(temperature=t, humidity=h)

    def battery(self):
        """float: the battery level [%]"""
        return self._unpack('<B', AssignedNumbers.batteryLevel)

    def rssi(self):
        """int: Received Signal Strength Indication for the last received broadcast from the device"""
        return self._scan_entry.rssi

    def info(self):
        """Returns a :class:`dict` of all parameters from the Smart Gadget.

        Calling this method can take a very long time.
        """
        t, h = self.temperature_humidity()
        info = {
            'device_name': self.NAME,  # equal to self._read(AssignedNumbers.deviceName).decode()
            'appearance': self._unpack('<H', AssignedNumbers.appearance),
            'peripheral_preferred_connection_parameters': self._unpack('<Q', AssignedNumbers.peripheralPreferredConnectionParameters),
            'system_id': self._unpack('<Q', AssignedNumbers.systemId),
            'manufacturer': self._read(AssignedNumbers.manufacturerNameString).decode(),
            'model': self._read(AssignedNumbers.modelNumberString).decode(),
            'serial': self._read(AssignedNumbers.serialNumberString).decode(),
            'hardware_revision': self._read(AssignedNumbers.hardwareRevisionString).decode(),
            'firmware_revision': self._read(AssignedNumbers.firmwareRevisionString).decode(),
            'software_revision': self._read(AssignedNumbers.softwareRevisionString).decode(),
            'temperature': t,
            'humidity': h,
            'dewpoint': self.dewpoint(temperature=t, humidity=h),
            'battery': self.battery(),
            'rssi': self.rssi()
        }

        try:
            info['oldest_timestamp_ms'] = self._unpack('<Q', self.OLDEST_TIMESTAMP_MS_CHARACTERISTIC_UUID)
            info['newest_timestamp_ms'] = self._unpack('<Q', self.NEWEST_TIMESTAMP_MS_CHARACTERISTIC_UUID)
            info['logger_interval_ms'] = self._unpack('<L', self.LOGGER_INTERVAL_MS_CHARACTERISTIC_UUID)
        except AttributeError:
            pass

        return info

    def _read(self, uuid):
        characteristic = self.getCharacteristics(uuid=uuid)[0]
        return characteristic.read()

    def _unpack(self, fmt, uid):
        return struct.unpack(fmt, self._read(uid))[0]


class SHTC1(SmartGadget):
    NAME = 'SHTC1 smart gadget'

    TEMPERATURE_HUMIDITY_CHARACTERISTIC_UUID = UUID('0000aa21-0000-1000-8000-00805f9b34fb')

    def temperature(self):
        return self.temperature_humidity()[0]

    def humidity(self):
        return self.temperature_humidity()[1]

    def temperature_humidity(self):
        t, h = struct.unpack('<hh', self._read(self.TEMPERATURE_HUMIDITY_CHARACTERISTIC_UUID))
        return t / 100., h / 100.


class SHT3X(SmartGadget):
    NAME = 'Smart Humigadget'

    # the following UUIDs are taken from
    # https://github.com/Sensirion/SmartGadget-Firmware/blob/master/Simple_BLE_Profile_Description.pdf

    OLDEST_TIMESTAMP_MS_CHARACTERISTIC_UUID = UUID('0000f236-b38d-4985-720e-0f993a68ee41')
    NEWEST_TIMESTAMP_MS_CHARACTERISTIC_UUID = UUID('0000f237-b38d-4985-720e-0f993a68ee41')
    LOGGER_INTERVAL_MS_CHARACTERISTIC_UUID = UUID('0000f239-b38d-4985-720e-0f993a68ee41')
    TEMPERATURE_CHARACTERISTIC_UUID = UUID('00002235-b38d-4985-720e-0f993a68ee41')
    HUMIDITY_CHARACTERISTIC_UUID = UUID('00001235-b38d-4985-720e-0f993a68ee41')

    def temperature(self):
        return self._unpack('<f', self.TEMPERATURE_CHARACTERISTIC_UUID)

    def humidity(self):
        return self._unpack('<f', self.HUMIDITY_CHARACTERISTIC_UUID)

    def temperature_humidity(self):
        return self.temperature(), self.humidity()
