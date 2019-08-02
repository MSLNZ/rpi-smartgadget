"""
The SHT3X series Smart Gadget from Sensirion.
"""
import time
from typing import Tuple, List

try:
    from bluepy.btle import Peripheral, UUID
except ImportError:  # then not on the Raspberry Pi
    Peripheral, UUID = object, lambda u: ()

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
        """Returns the current temperature [degree C]."""
        return self._read(self.TEMPERATURE_HANDLE, '<f')

    def humidity(self) -> float:
        """Returns the current humidity [%RH]."""
        return self._read(self.HUMIDITY_HANDLE, '<f')

    def temperature_humidity(self) -> Tuple[float, float]:
        """Returns the current temperature [degree C] and humidity [%RH]."""
        return self.temperature(), self.humidity()

    def battery(self) -> int:
        """Returns the battery level [%]"""
        return self._read(self.BATTERY_LEVEL_HANDLE, '<B')

    def info(self) -> dict:
        """Returns all available information from the Smart Gadget."""
        # ignore Appearance and Peripheral Preferred Connection Parameters since they are not relevant
        t, h = self.temperature_humidity()
        return {
            'battery': self.battery(),
            'device_name': self.DEVICE_NAME,  # equal to self._read(self.DEVICE_NAME_HANDLE)
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
        """Returns the oldest timestamp [milliseconds]."""
        return self._read(self.OLDEST_TIMESTAMP_MS_HANDLE, '<Q')

    def set_oldest_timestamp(self, milliseconds: int):
        """Set the oldest timestamp [milliseconds]."""
        data = 0 if milliseconds is None else int(milliseconds)
        self._write(self.OLDEST_TIMESTAMP_MS_HANDLE, '<Q', data)

    def newest_timestamp(self) -> int:
        """Returns the newest timestamp [milliseconds]."""
        return self._read(self.NEWEST_TIMESTAMP_MS_HANDLE, '<Q')

    def set_newest_timestamp(self, milliseconds: int):
        """Set the newest timestamp [milliseconds]."""
        self._write(self.NEWEST_TIMESTAMP_MS_HANDLE, '<Q', int(milliseconds))

    def logger_interval(self) -> int:
        """Returns the logger interval [milliseconds]"""
        return self._read(self.LOGGER_INTERVAL_MS_HANDLE, '<L')

    def set_logger_interval(self, milliseconds: int):
        """Set the logger interval [milliseconds].

        This will reset all values that are currently saved in memory.
        """
        self._write(self.LOGGER_INTERVAL_MS_HANDLE, '<L', int(milliseconds))

    def temperature_notifications_enabled(self) -> bool:
        """Returns whether temperature notifications are enabled (True) or disabled (False)."""
        return bool(self._read(self.TEMPERATURE_NOTIFICATION_HANDLE, '<H'))

    def enable_temperature_notifications(self):
        """Enable temperature notifications."""
        self._write(self.TEMPERATURE_NOTIFICATION_HANDLE, '<H', 1)

    def disable_temperature_notifications(self):
        """Disable temperature notifications."""
        self._write(self.TEMPERATURE_NOTIFICATION_HANDLE, '<H', 0)

    def humidity_notifications_enabled(self) -> bool:
        """Returns whether humidity notifications are enabled (True) or disabled (False)."""
        return bool(self._read(self.HUMIDITY_NOTIFICATION_HANDLE, '<H'))

    def enable_humidity_notifications(self):
        """Enable humidity notifications."""
        self._write(self.HUMIDITY_NOTIFICATION_HANDLE, '<H', 1)

    def disable_humidity_notifications(self):
        """Disable humidity notifications."""
        self._write(self.HUMIDITY_NOTIFICATION_HANDLE, '<H', 0)

    def set_sync_time(self, milliseconds: int = None):
        """Sync the timestamps of the logged data.

        If :data:`None` then uses the current time of the Raspberry Pi.
        """
        data = round(time.time() * 1000) if milliseconds is None else int(milliseconds)
        self._write(self.SYNC_TIME_MS_HANDLE, '<Q', data)

    def fetch_logged_data(self, sync_ms=None, oldest_ms=None, newest_ms=None) -> Tuple[List[float], List[float]]:
        """Returns the logged temperature and humidity values."""
        self.enable_temperature_notifications()
        self.enable_humidity_notifications()
        self.set_sync_time(sync_ms)
        self.set_oldest_timestamp(oldest_ms)
        if newest_ms is not None:
            self.set_newest_timestamp(newest_ms)
        self.delegate.initialize()
        self._write(self.START_LOGGER_DOWNLOAD_HANDLE, '<B', 1)
        while True:
            self.waitForNotifications(1)
            if self.delegate.finished:
                break
        return self.delegate.temperatures, self.delegate.humidities


class SHT3XService(SmartGadgetService):

    def __init__(self):
        super(SHT3XService, self).__init__(SHT3X)

    def oldest_timestamp(self, mac_address: str) -> int:
        """Returns the oldest timestamp [milliseconds]."""
        return self._process('oldest_timestamp', mac_address)

    def set_oldest_timestamp(self, mac_address: str, milliseconds: int):
        """Set the oldest timestamp [milliseconds]."""
        self._process('set_oldest_timestamp', mac_address, milliseconds=milliseconds)

    def newest_timestamp(self, mac_address: str) -> int:
        """Returns the newest timestamp [milliseconds]."""
        return self._process('newest_timestamp', mac_address)

    def set_newest_timestamp(self, mac_address: str, milliseconds: int):
        """Set the newest timestamp [milliseconds]."""
        self._process('set_newest_timestamp', mac_address, milliseconds=milliseconds)

    def logger_interval(self, mac_address: str) -> int:
        """Returns the logger interval [milliseconds]"""
        return self._process('logger_interval', mac_address)

    def set_logger_interval(self, mac_address: str, milliseconds: int):
        """Set the logger interval [milliseconds].

        This will reset all values that are currently saved in memory.
        """
        self._process('set_logger_interval', mac_address, milliseconds=milliseconds)

    def temperature_notifications_enabled(self, mac_address: str) -> bool:
        """Returns whether temperature notifications are enabled (True) or disabled (False)."""
        return self._process('temperature_notifications_enabled', mac_address)

    def enable_temperature_notifications(self, mac_address: str):
        """Enable temperature notifications."""
        self._process('enable_temperature_notifications', mac_address)

    def disable_temperature_notifications(self, mac_address: str):
        """Disable temperature notifications."""
        self._process('disable_temperature_notifications', mac_address)

    def humidity_notifications_enabled(self, mac_address: str) -> bool:
        """Returns whether humidity notifications are enabled (True) or disabled (False)."""
        return self._process('humidity_notifications_enabled', mac_address)

    def enable_humidity_notifications(self, mac_address: str):
        """Enable humidity notifications."""
        self._process('enable_humidity_notifications', mac_address)

    def disable_humidity_notifications(self, mac_address: str):
        """Disable humidity notifications."""
        self._process('disable_humidity_notifications', mac_address)

    def set_sync_time(self, mac_address: str, milliseconds: int = None):
        """Sync the timestamps of the logged data.

        If :data:`None` then uses the current time of the Raspberry Pi.
        """
        self._process('set_sync_time', mac_address, milliseconds=milliseconds)

    def fetch_logged_data(self, mac_address: str, sync_ms=None,
                          oldest_ms=None, newest_ms=None) -> Tuple[List[float], List[float]]:
        """Returns the logged temperature and humidity values."""
        return self._process('fetch_logged_data', mac_address, sync_ms=sync_ms,
                             oldest_ms=oldest_ms, newest_ms=newest_ms)