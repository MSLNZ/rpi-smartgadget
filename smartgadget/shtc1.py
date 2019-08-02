"""
The SHTC1 series Smart Gadget from Sensirion.

Don't have a SHTC1 device to test this class.
If/when we do then we could provide this as a MSL-Network Service as well.
"""
from typing import Tuple
try:
    from bluepy.btle import UUID
except ImportError:  # then not on the Raspberry Pi
    UUID = lambda u: ()

from .smart_gadget import SmartGadget
from .service import SmartGadgetService

TEMPERATURE_HUMIDITY_CHARACTERISTIC_UUID = UUID('0000aa21-0000-1000-8000-00805f9b34fb')


class SHTC1(SmartGadget):

    # This equals the value of DEVICE_NAME_CHARACTERISTIC_UUID
    DEVICE_NAME = 'SHTC1 smart gadget'

    def temperature(self) -> float:
        """float: Returns the current temperature, in degree C."""
        return self.temperature_humidity()[0]

    def humidity(self) -> float:
        """float: Returns the current humidity, in %RH."""
        return self.temperature_humidity()[1]

    def temperature_humidity(self) -> Tuple[float, float]:
        """float, float: Returns the current temperature and humidity."""
        t, h = self._read(TEMPERATURE_HUMIDITY_CHARACTERISTIC_UUID, '<hh')
        return t / 100., h / 100.

    def battery(self) -> int:
        """Returns the battery level [%]"""
        return self._read(self.BATTERY_LEVEL_CHARACTERISTIC_UUID, '<B')

    def info(self) -> dict:
        """Returns all available information from the Smart Gadget."""
        # ignore Appearance and Peripheral Preferred Connection Parameters since they are not relevant
        t, h = self.temperature_humidity()
        return {
            'battery': self.battery(),
            'device_name': self.DEVICE_NAME,  # equal to self._read(DEVICE_NAME_HANDLE)
            'dewpoint': self.dewpoint(temperature=t, humidity=h),
            'firmware_revision': self._read(self.FIRMWARE_REVISION_STRING_CHARACTERISTIC_UUID),
            'hardware_revision': self._read(self.HARDWARE_REVISION_STRING_CHARACTERISTIC_UUID),
            'humidity': h,
            'manufacturer': self._read(self.MANUFACTURER_NAME_STRING_CHARACTERISTIC_UUID),
            'model_number': self._read(self.MODEL_NUMBER_STRING_CHARACTERISTIC_UUID),
            'rssi': self.rssi(),
            'serial_number': self._read(self.SERIAL_NUMBER_STRING_CHARACTERISTIC_UUID),
            'software_revision': self._read(self.SOFTWARE_REVISION_STRING_CHARACTERISTIC_UUID),
            'system_id': self._read(self.SYSTEM_ID_CHARACTERISTIC_UUID, '<Q'),
            'temperature': t,
        }


class SHTC1Service(SmartGadgetService):

    def __init__(self):
        super(SHTC1Service, self).__init__(SHTC1)
