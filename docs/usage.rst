.. _rpi-smartgadget-usage:

===========
Basic Usage
===========

Place a Raspberry Pi in a location where the Smart Gadgets are within Bluetooth range.

On another computer that is on the same network as the Raspberry Pi run the following

.. note::

   You will have to change the value of *host* below for your Raspberry Pi. The reason for including
   ``assert_hostname=False`` is because we show that we are specifying an IP address for the value
   of `host` instead of its hostname. The hostname of the Raspberry Pi is *(most likely)* ``'raspberrypi'``
   and so ``'xxx.xxx.xxx.xxx'`` won't equal ``'raspberrypi'`` when the security of the connection is
   checked behind the scenes. If you specify the hostname of the Raspberry Pi then you can do hostname
   verification and not include the ``assert_hostname=False`` keyword argument. In general, use
   ``assert_hostname=False`` at your own risk if there is a possibility of a man-in-the-middle hijack
   between your computer and the remote computer.

.. code-block:: pycon

   >>> from smartgadget import connect
   >>> rpi = connect(host='xxx.xxx.xxx.xxx', assert_hostname=False)

To find out what can be requested from a Smart Gadget, run the following

.. code-block:: pycon

    >>> print(rpi.manager(as_string=True, indent=2))
    Manager[raspberrypi:1875]
      attributes:
        identity() -> dict
        link(service: str) -> bool
      language: Python 3.7.3
      os: Linux 4.19.97-v7+ armv7l
    Clients [1]:
      LinkedClient[192.168.1.69:63117]
        language: Python 3.7.7
        os: Windows 10 AMD64
    Services [1]:
      Smart Humigadget[raspberrypi:36834]
        attributes:
          battery(mac_address) -> int
          connect_gadget(mac_address, strict=True) -> bool
          connect_gadgets(mac_addresses, strict=True) -> Tuple[list, list]
          connected_gadgets() -> List[str]
          dewpoint(mac_address, temperature=None, humidity=None) -> float
          disable_humidity_notifications(mac_address)
          disable_temperature_notifications(mac_address)
          disconnect_gadget(mac_address)
          disconnect_gadgets()
          enable_humidity_notifications(mac_address)
          enable_temperature_notifications(mac_address)
          fetch_logged_data(mac_address, *, enable_temperature=True, enable_humidity=True, sync=None, oldest=None, newest=None, as_datetime=False, num_iterations=1) -> Tuple[list, list]
          humidity(mac_address) -> float
          humidity_notifications_enabled(mac_address) -> bool
          info(mac_address) -> dict
          logger_interval(mac_address) -> int
          max_attempts() -> int
          newest_timestamp(mac_address) -> int
          oldest_timestamp(mac_address) -> int
          restart_bluetooth()
          rpi_date() -> str
          rssi(mac_address) -> int
          scan(timeout=10, passive=False) -> List[str]
          set_logger_interval(mac_address, milliseconds)
          set_max_attempts(max_attempts)
          set_newest_timestamp(mac_address, timestamp)
          set_oldest_timestamp(mac_address, timestamp)
          set_rpi_date(date)
          set_sync_time(mac_address, timestamp=None)
          shutdown_service()
          temperature(mac_address) -> float
          temperature_humidity(mac_address) -> Tuple[float, float]
          temperature_humidity_dewpoint(mac_address) -> Tuple[float, float, float]
          temperature_notifications_enabled(mac_address) -> bool
        language: Python 3.7.3
        max_clients: -1
        os: Linux 4.19.97-v7+ armv7l

The information about the :class:`~msl.network.manager.Manager` and which
:class:`~msl.network.client.Client`\s and :class:`~msl.network.service.Service`\s
are connected to it will be shown. The ``Smart Humigadget`` :class:`~msl.network.service.Service`
indicates that it has the following methods that can be called: *battery*, *connect_gadget*, etc...

Next, we scan for all available Smart Gadgets, request the temperature, humidity and dew point and then
disconnect from the Raspberry Pi

.. code-block:: pycon

   >>> mac_addresses = rpi.scan()
   >>> for address in mac_addresses:
   ...    print(address, rpi.temperature_humidity_dewpoint(address))
   c7:99:a8:77:e9:2a [20.329999923706055, 49.81999969482422, 9.521468351961703]
   cc:ea:2e:0c:11:f6 [19.56999969482422, 48.77000045776367, 8.507598739882166]
   ed:8d:dd:6a:58:25 [20.229999542236328, 46.060001373291016, 8.267915590472189]
   ea:12:51:be:f9:6e [20.40999984741211, 47.060001373291016, 8.749198797952799]
   ef:ce:43:b4:83:f8 [21.399999618530273, 39.84000015258789, 7.196289989617892]
   >>> rpi.disconnect()
