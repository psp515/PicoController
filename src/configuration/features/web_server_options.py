from configuration.base_options import BaseOptions

DEFAULT_BUTTON_PIN = "14"
DEFAULT_STRIP_PIN = "18"

DEFAULT_WIFI_SSID = "LedController"
DEFAULT_WIFI_PASSWORD = "123456789"


class WebServerOptions(BaseOptions):
    NAME = "webserver"

    def __init__(self):
        super().__init__()

    @property
    def ssid(self):
        try:
            ssid = self.manager.read_config(self.app_settings_name)[self.NAME]["ssid"]

            if ssid == "":
                return DEFAULT_WIFI_SSID

            return ssid
        except KeyError:
            return DEFAULT_WIFI_SSID

    @property
    def password(self):
        try:
            password = self.manager.read_config(self.app_settings_name)[self.NAME]["password"]

            if password == "":
                return DEFAULT_WIFI_PASSWORD

            return password
        except KeyError:
            return DEFAULT_WIFI_PASSWORD

    def empty(self) -> bool:
        return False
