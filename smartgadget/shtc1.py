"""
The SHTC1 series Smart Gadget from Sensirion.

Don't have a SHTC1 device to test this class.
When we do, we could provide this as a MSL-Network Service as well.
"""
from typing import Tuple
try:
    from bluepy.btle import UUID
except ImportError:  # then not on the Raspberry Pi
    UUID = lambda u: u

from .smart_gadget import SmartGadget
from .service import SmartGadgetService


class SHTC1(SmartGadget):

    # This equals the value of DEVICE_NAME_CHARACTERISTIC_UUID
    DEVICE_NAME = 'SHTC1 smart gadget'

    TEMPERATURE_HUMIDITY_CHARACTERISTIC_UUID = UUID('0000aa21-0000-1000-8000-00805f9b34fb')

    def temperature(self) -> float:
        """Returns the current temperature.

        Returns
        -------
        :class:`float`
            The current temperature [degree C].
        """
        return self.temperature_humidity()[0]

    def humidity(self) -> float:
        """Returns the current humidity.

        Returns
        -------
        :class:`float`
            The current humidity [%RH].
        """
        return self.temperature_humidity()[1]

    def temperature_humidity(self) -> Tuple[float, float]:
        """Returns the current temperature and humidity.

        Returns
        -------
        :class:`float`
            The current temperature [degree C].
        :class:`float`
            The current humidity [%RH].
        """
        t, h = self._read(self.TEMPERATURE_HUMIDITY_CHARACTERISTIC_UUID, '<hh')
        return t / 100., h / 100.

    def battery(self) -> int:
        """Returns the battery level.

        Returns
        -------
        :class:`float`
            The current battery level [%].
        """
        return self._read(self.BATTERY_LEVEL_CHARACTERISTIC_UUID, '<B')

    def info(self) -> dict:
        """Returns all available information from the Smart Gadget.

        Returns
        -------
        :class:`dict`
            Includes information such as the firmware, hardware and software version numbers,
            the battery level, the temperature, humidity and dew point values.
        """
        # ignore Appearance and Peripheral Preferred Connection Parameters since they are not relevant
        t, h = self.temperature_humidity()
        return {
            'battery': self.battery(),
            'device_name': self.DEVICE_NAME,
            'dewpoint': self.dewpoint(temperature=t, humidity=h),
            'firmware_revision': self._read(self.FIRMWARE_REVISION_STRING_CHARACTERISTIC_UUID),
            'hardware_revision': self._read(self.HARDWARE_REVISION_STRING_CHARACTERISTIC_UUID),
            'humidity': h,
            'mac_address': self.addr,
            'manufacturer': self._read(self.MANUFACTURER_NAME_STRING_CHARACTERISTIC_UUID),
            'model_number': self._read(self.MODEL_NUMBER_STRING_CHARACTERISTIC_UUID),
            'rssi': self.rssi(),
            'serial_number': self._read(self.SERIAL_NUMBER_STRING_CHARACTERISTIC_UUID),
            'software_revision': self._read(self.SOFTWARE_REVISION_STRING_CHARACTERISTIC_UUID),
            'system_id': self._read(self.SYSTEM_ID_CHARACTERISTIC_UUID, '<Q'),
            'temperature': t,
        }


class SHTC1Service(SmartGadgetService):

    def __init__(self, interface=None):
        """The :class:`~msl.network.service.Service` for a :class:`.SHTC1` Smart Gadget.

        Parameters
        ----------
        interface : :class:`int`, optional
            The Bluetooth interface to use for the connection. For example, 0 or :data:`None`
            means ``/dev/hci0``, 1 means ``/dev/hci1``.
        """
        super(SHTC1Service, self).__init__(SHTC1, interface=interface)
