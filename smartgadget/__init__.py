import logging
from math import exp, log10

from msl.network import manager, ssh

# if you change this value then you must also update the name of the
# virtual environment that is created in rpi-setup.sh
RPI_EXE_PATH = 'shtenv/bin/smartgadget'

logger = logging.getLogger(__package__)


def connect(*, host='raspberrypi', rpi_username='pi', rpi_password=None, timeout=10, **kwargs):
    """Connect to the :class:`~smartgadget.sht3x.SHT3XService` on the Raspberry Pi.

    :param str host: The hostname or IP address of the Raspberry Pi.
    :param str rpi_username: The username for the Raspberry Pi.
    :param str rpi_password: The password for `rpi_username`.
    :param float timeout: The maximum number of seconds to wait for the connection.
    :param kwargs: Keyword arguments that are passed to :func:`~msl.network.manager.run_services`.

    :return: A connection to the :class:`~smartgadget.sht3x.SHT3XService` on the Raspberry Pi.
    :rtype: :class:`~smartgadget.client.SmartGadgetClient`
    """
    console_script_path = '/home/{}/{}'.format(rpi_username, RPI_EXE_PATH)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, timeout=timeout, as_sudo=True, **kwargs)

    kwargs['host'] = host
    return SmartGadgetClient('Smart Humigadget', **kwargs)


def start_service_on_rpi():
    """Starts the Network :class:`~msl.network.manager.Manager` and the :class:`~smartgadget.sht3x.SHT3XService`.

    This function should only be called from the ``smartgadget`` console script (see setup.py).
    """
    kwargs = ssh.parse_console_script_kwargs()
    if kwargs.get('auth_login', False) and ('username' not in kwargs or 'password' not in kwargs):
        raise ValueError(
            'The Manager is using a login for authentication but the SmartGadgetService '
            'does not know the username and password to use to connect to the Manager'
        )
    manager.run_services(SHT3XService(), **kwargs)


def kill_manager(*, host='raspberrypi', rpi_username='pi', rpi_password=None, timeout=10, **kwargs):
    """Kill the Network :class:`~msl.network.manager.Manager` on the Raspberry Pi.

    :param str host: The hostname or IP address of the Raspberry Pi.
    :param str rpi_username: The username for the Raspberry Pi.
    :param str rpi_password: The password for `rpi_username`.
    :param float timeout: The maximum number of seconds to wait for the connection.
    :param kwargs: Keyword arguments that are passed to :meth:`~paramiko.client.SSHClient.connect`.
    """
    ssh_client = ssh.connect(host, username=rpi_username, password=rpi_password, timeout=timeout, **kwargs)
    lines = ssh.exec_command(ssh_client, 'ps aux | grep smartgadget')
    pids = []
    for line in lines:
        if RPI_EXE_PATH in line:
            pids.append(line.split()[1])
    for pid in pids:
        try:
            ssh.exec_command(ssh_client, 'sudo kill -9 ' + pid)
        except:
            pass
    ssh_client.close()


def dewpoint(temperature, humidity):
    """Calculate the dew point.

    :param float temperature: The temperature [degree C].
    :param float humidity: The humidity [%RH].
    :return: The dew point [degree C].
    :rtype: float
    """
    # TODO get formula from JLS.
    #  For now use Equation 7 from
    #  https://www.vaisala.com/sites/default/files/documents/Humidity_Conversion_Formulas_B210973EN-F.pdf

    if temperature < -20 or temperature > 350:
        # the Equation 7 is only valid between -20 and +350 degree C
        raise ValueError('temperature={} is not between -20 and +350 degree C'.format(temperature))

    # calculate Pws using Equation 3
    C1 = -7.85951783
    C2 = 1.84408259
    C3 = -11.7866497
    C4 = 22.6807411
    C5 = -15.9618719
    C6 = 1.80122502
    Pc = 220640.
    Tc = 647.096
    kelvin = temperature + 273.15
    x = 1.0 - kelvin / Tc
    y = (Tc / kelvin) * (C1 * x + C2 * x**1.5 + C3 * x**3 + C4 * x**3.5 + C5 * x**4 + C6 * x**7.5)
    Pws = Pc * exp(y)

    # calculate Pw using Equation 1
    Pw = Pws * humidity / 100.

    # calculate the dew point using Equation 7
    if -20 <= temperature <= 50:
        A, m, Tn = 6.116441, 7.591386, 240.7263
    elif 50 < temperature < 100:
        A, m, Tn = 6.004918, 7.337936, 229.3975
    elif 100 <= temperature <= 150:
        A, m, Tn = 5.856548, 7.277310, 225.1033
    elif 150 < temperature <= 200:
        A, m, Tn = 6.002859, 7.290361, 227.1704
    elif 200 < temperature <= 350:
        A, m, Tn = 9.980622, 7.388931, 263.1239
    else:
        assert False, 'should never get here'

    return Tn / (m / log10(Pw / A) - 1.0)


from .client import SmartGadgetClient
from .sht3x import SHT3XService
