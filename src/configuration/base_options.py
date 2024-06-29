from configuration.configuration_manager import ConfigurationManager


class BaseOptions:
    def __init__(self):
        self.manager = ConfigurationManager()
        self.app_settings_name = "app_settings"

    def empty(self) -> bool:
        return True
