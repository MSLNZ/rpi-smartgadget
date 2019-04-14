from msl.network import connect, client, MSLNetworkError


class SmartGadgetClient(object):

    def __init__(self, host, **kwargs):
        """Connect to the Raspberry Pi and link with the SmartGadget Service

        :param str hostname: The hostname or IP address of the Raspberry Pi.
        :param kwargs: Keyword arguments that are passed to msl.network.client.connect
        """
        super(SmartGadgetClient, self).__init__()

        self._link = None

        # just in case kwargs['host'] exists -- since we are already
        # explicitly passing in host=hostname
        kwargs.pop('host', None)

        self._cxn = connect(host=host, **client.filter_client_connect_kwargs(**kwargs))
        self._link = self._cxn.link('SmartGadget')

    def __getattr__(self, item):
        def request(*args, **kwargs):
            try:
                return getattr(self._link, item)(*args, **kwargs)
            except MSLNetworkError:
                self.disconnect()
                raise
        return request

    def manager(self, as_yaml=False, indent=4, timeout=None):
        return self._cxn.manager(as_yaml=as_yaml, indent=indent, timeout=timeout)

    def admin_request(self, attrib, *args, **kwargs):
        return self._cxn.admin_request(attrib, *args, **kwargs)

    def disconnect(self):
        if self._link is not None:
            self._link.disconnect_service()
            self._link = None

    def __del__(self):
        self.disconnect()
