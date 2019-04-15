from msl.network import LinkedClient


class SmartGadgetClient(LinkedClient):

    def __init__(self, service_name, **kwargs):
        """Connect to the Raspberry Pi and link with the SmartGadget
        :class:`~msl.network.service.Service`.

        :param str service_name: The name of the :class:`~msl.network.service.Service` to link with.
        :param kwargs: Keyword arguments that are passed to :func:`~msl.network.client.connect`.
        """
        super().__init__(service_name, **kwargs)

    def disconnect(self):
        """
        Shut down the SmartGadget :class:`~msl.network.service.Service`
        and the Network :class:`~msl.network.manager.Manager`.
        """
        self.disconnect_service()
        super().disconnect()

    def service_error_handler(self):
        """
        Shut down the SmartGadget :class:`~msl.network.service.Service`
        and the Network :class:`~msl.network.manager.Manager` if there was
        an error.
        """
        self.disconnect()
