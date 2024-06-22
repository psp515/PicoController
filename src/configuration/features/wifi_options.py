from configuration.base_options import BaseOptions


class WifiOptions(BaseOptions):
    NAME = "wifi"

    def __init__(self):
        super().__init__()

    @property
    def ssid(self):
        return self.manager.read_config(self.NAME).get("ssid", "")

    @ssid.setter
    def ssid(self, value):
        self.manager.update_config(self.NAME, "ssid", value)

    @property
    def password(self):
        return self.manager.read_config(self.NAME).get("password", "")

    @password.setter
    def password(self, value):
        self.manager.update_config(self.NAME, "password", value)

    def empty(self) -> bool:
        return self.ssid == "" or self.password == ""
