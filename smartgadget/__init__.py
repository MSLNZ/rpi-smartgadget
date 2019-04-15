from msl.network import manager, ssh

from .service import SmartGadgetService
from .client import SmartGadgetClient


def connect(*, host='raspberrypi', rpi_username='pi', rpi_password=None, timeout=10, **kwargs):
    """Connect to the Smart-Gadget Service on the Raspberry Pi.

    :param str host: The hostname or IP address of the Raspberry Pi.
    :param str rpi_username: The username for the Raspberry Pi.
    :param str rpi_password: The password for `rpi_username`.
    :param float timeout: The maximum number of seconds to wait for the connection.
    :param kwargs: Keyword arguments that are passed to the msl.network.manager.run_services function.

    :returns: SmartGadgetClient
    """
    console_script_path = '/home/{}/shtenv/bin/smartgadget'.format(rpi_username)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, timeout=timeout, as_sudo=True, **kwargs)

    kwargs['host'] = host
    return SmartGadgetClient(**kwargs)


def start_service_on_rpi():
    """Starts the MSL-Network Manager and the Smart-Gadget Service.

    This function should only be called from the `smartgadget` console script (see setup.py).
    """
    kwargs = ssh.parse_console_script_kwargs()
    if kwargs.get('auth_login', False) and ('username' not in kwargs or 'password' not in kwargs):
        raise ValueError(
            'The Manager is using a login for authentication but the SmartGadgetService '
            'does not know the username and password to use to connect to the Manager'
        )

    manager.run_services(SmartGadgetService(), **kwargs)
