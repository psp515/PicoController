from configuration.configuration_manager import ConfigurationManager


class BaseOptions:
    def __init__(self):
        self.manager = ConfigurationManager()
