

class BaseInterface(object):
    """The basic interface for carriers. All registered carriers should inherit
    from this class.
    """
    # DEFAULT_CFG = NullConfig()

    def __init__(self, config):
        self._config = config


    def __str__(self):
        raise NotImplementedError

    @staticmethod
    def require_valid_tracking_number(func):
        """Intended for wrapping subclasses' track() methods, ensures track()
        is called with a valid tracking number for that carrier.
        """
        # @wraps(func)
        def wrapper(self, tracking_number, skip_check=False, *pargs, **kwargs):
            if not self.identify(tracking_number):
                # raise InvalidTrackingNumber(tracking_number)
                raise RuntimeError("Invalid Tracking Number: {}".format(tracking_number))
            else:
                return func(self, tracking_number, *pargs, **kwargs)
        return wrapper

    def identify(self, tracking_number):
        raise NotImplementedError()

    def search_for_tracking(self, content):
        raise NotImplementedError()

    def verify_tracking_number(self, tracking_number):
        raise NotImplementedError()

    def track(self, tracking_number):
        raise NotImplementedError()

    def is_delivered(self, tracking_number, tracking_info=None):
        raise NotImplementedError()

    # def url(self, tracking_number):
    #     return self._url_template.format(tracking_number=tracking_number)

    # def _cfg_value(self, *keys):
    #     """Return the config value from this carrier, looked up with {keys}.
    #     If the value is not found, the DEFAULT_CFG is fallen back to, then
    #     a ConfigKeyError is raised if still not found.
    #     """
    #     try:
    #         value = self._config.get_value(self.CONFIG_NS, *keys)
    #     except ConfigKeyError as err:
    #         try:
    #             value = self.DEFAULT_CFG.get_value(self.CONFIG_NS, *keys)
    #         except ConfigKeyError:
    #             raise err
    #     return value
