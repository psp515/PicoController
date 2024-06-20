from configuration.base_options import BaseOptions


class MqttOptions(BaseOptions):
    NAME = "mqtt"

    def __init__(self):
        super().__init__()

    @property
    def host(self):
        return self.manager.read_config(self.NAME)["host"]

    @host.setter
    def host(self, value):
        self.manager.update_config(self.NAME, "host", value)

    @property
    def port(self):
        return self.manager.read_config(self.NAME)["port"]

    @port.setter
    def port(self, value):
        self.manager.update_config(self.NAME, "port", value)

    @property
    def username(self):
        return self.manager.read_config(self.NAME)["username"]

    @username.setter
    def username(self, value):
        self.manager.update_config(self.NAME, "username", value)

    @property
    def password(self):
        return self.manager.read_config(self.NAME)["password"]

    @password.setter
    def password(self, value):
        self.manager.update_config("mqtt", "password", value)
