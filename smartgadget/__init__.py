from msl.network import manager, ssh

from .service import SmartGadgetService
from .client import SmartGadgetClient
from .sht3x import SHT3X
from .shtc1 import SHTC1

RPI_EXE_PATH = 'shtenv/bin/smartgadget'


def connect(*, host='raspberrypi', rpi_username='pi', rpi_password=None, timeout=10, **kwargs):
    """Connect to the :class:`~.service.SmartGadgetService` on the Raspberry Pi.

    :param str host: The hostname or IP address of the Raspberry Pi.
    :param str rpi_username: The username for the Raspberry Pi.
    :param str rpi_password: The password for `rpi_username`.
    :param float timeout: The maximum number of seconds to wait for the connection.
    :param kwargs: Keyword arguments that are passed to :func:`~msl.network.manager.run_services`.

    :return: A connection to the :class:`~.service.SmartGadgetService` on the Raspberry Pi.
    :rtype: :class:`~.client.SmartGadgetClient`
    """
    console_script_path = '/home/{}/{}'.format(rpi_username, RPI_EXE_PATH)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, timeout=timeout, as_sudo=True, **kwargs)

    kwargs['host'] = host
    return SmartGadgetClient('SmartGadget', **kwargs)


def start_service_on_rpi():
    """Starts the Network :class:`~msl.network.manager.Manager` and the :class:`~.service.SmartGadgetService`.

    This function should only be called from the ``smartgadget`` console script (see setup.py).
    """
    kwargs = ssh.parse_console_script_kwargs()
    if kwargs.get('auth_login', False) and ('username' not in kwargs or 'password' not in kwargs):
        raise ValueError(
            'The Manager is using a login for authentication but the SmartGadgetService '
            'does not know the username and password to use to connect to the Manager'
        )

    manager.run_services(SmartGadgetService(), **kwargs)


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
