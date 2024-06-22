from configuration.base_options import BaseOptions


class AppSettings(BaseOptions):
    NAME = "app_settings"

    def __init__(self):
        super().__init__()

    @property
    def button_pin(self) -> str:
        return self.manager.read_config(self.NAME)["button_pin"]

    @button_pin.setter
    def button_pin(self, value: str):
        self.manager.update_config(self.NAME, "button_pin", value)

    @property
    def strip_pin(self) -> str:
        return self.manager.read_config(self.NAME)["button_pin"]

    @strip_pin.setter
    def strip_pin(self, value: str):
        self.manager.update_config(self.NAME, "button_pin", value)

    def empty(self) -> bool:
        return self.button_pin == "" or self.strip_pin == ""
