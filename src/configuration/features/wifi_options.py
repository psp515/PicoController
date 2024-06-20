from configuration.base_options import BaseOptions


class WifiOptions(BaseOptions):
    NAME = "wifi"

    def __init__(self):
        super().__init__()

    @property
    def ssid(self):
        return self.manager.read_config(self.NAME)["username"]

    @ssid.setter
    def ssid(self, value):
        self.manager.update_config(self.NAME, "username", value)

    @property
    def password(self):
        return self.manager.read_config(self.NAME)["password"]

    @password.setter
    def password(self, value):
        self.manager.update_config(self.NAME, "password", value)
