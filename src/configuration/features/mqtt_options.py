from configuration.base_options import BaseOptions


class MqttOptions(BaseOptions):
    NAME = "mqtt"

    def __init__(self):
        super().__init__()

    @property
    def url(self):
        return self.manager.read_config(self.NAME).get("url", "")

    @url.setter
    def url(self, value):
        self.manager.update_config(self.NAME, "url", value)

    @property
    def port(self):
        return self.manager.read_config(self.NAME).get("port", "")

    @port.setter
    def port(self, value):
        self.manager.update_config(self.NAME, "port", value)

    @property
    def username(self):
        return self.manager.read_config(self.NAME).get("username", "")

    @username.setter
    def username(self, value):
        self.manager.update_config(self.NAME, "username", value)

    @property
    def password(self):
        return self.manager.read_config(self.NAME).get("password", "")

    @password.setter
    def password(self, value):
        self.manager.update_config(self.NAME, "password", value)

    def empty(self) -> bool:
        return self.url == "" and self.port == "" and self.username == "" and self.password == ""
