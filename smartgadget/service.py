import subprocess
from typing import List, Tuple

from msl.network import Service
try:
    from bluepy.btle import Scanner
except ImportError:
    pass  # not on the Raspberry Pi

from .smart_gadget import SmartGadget


class SmartGadgetService(Service):

    def __init__(self):
        super(SmartGadgetService, self).__init__(name='SmartGadget')
        self._scanner = Scanner()
        self._devices = {}

    def scan(self, timeout=10, passive=False) -> List[str]:
        """Returns a list of MAC addresses of the Smart Gadgets that were found."""
        self._disconnect_devices()
        for dev in self._scanner.scan(timeout=timeout, passive=passive):
            device = SmartGadget.create(dev)
            if device is not None:
                self._devices[dev.addr] = device

        return [dev.addr for dev in self._devices.values()]

    def temperature(self, mac_address) -> float:
        """Returns the temperature [deg C] for the specified MAC address."""
        return self._devices[mac_address].temperature()

    def humidity(self, mac_address) -> float:
        """Returns the humidity [%RH] for the specified MAC address."""
        return self._devices[mac_address].humidity()

    def dewpoint(self, mac_address, temperature=None, humidity=None) -> float:
        """Returns the dew point [deg C] for the specified MAC address."""
        return self._devices[mac_address].dewpoint(temperature=temperature, humidity=humidity)

    def temperature_humidity(self, mac_address) -> Tuple[float]:
        """Returns the temperature [deg C] and humidity [%RH] for the specified MAC address."""
        return self._devices[mac_address].temperature_humidity()

    def temperature_humidity_dewpoint(self, mac_address) -> Tuple[float]:
        """Returns the temperature [deg C] and humidity [%RH] for the specified MAC address."""
        return self._devices[mac_address].temperature_humidity_dewpoint()

    def battery(self, mac_address) -> int:
        """Returns the battery level [%] for the specified MAC address."""
        return self._devices[mac_address].battery()

    def rssi(self, mac_address) -> int:
        """Received Signal Strength Indication for the last received broadcast from the device.

        This is an integer value measured in dB, where 0 dB is the maximum (theoretical) signal
        strength, and more negative numbers indicate a weaker signal.
        """
        return self._devices[mac_address].rssi

    def info(self, mac_address) -> dict:
        """Returns a :class:`dict` of all parameters from the Smart Gadget
        for the specified MAC address.

        Calling this method can take a very long time.
        """
        return self._devices[mac_address].info()

    def disconnect_service(self):
        """Shutdown the SmartGadget Service and the MSL-Network Manager."""
        self._disconnect_devices()
        self._disconnect()

    def restart_bluetooth(self):
        """Restart the bluetooth driver on the Raspberry Pi.

        This can fix scanning issues or connection timeouts.

        You will loose the connection to all devices that you are
        currently connected to.
        """
        self._disconnect_devices()
        subprocess.call(['sudo', 'systemctl', 'restart', 'bluetooth'])

    def _disconnect_devices(self):
        for device in self._devices.values():
            try:
                device.disconnect()
            except:
                pass
        self._devices.clear()
