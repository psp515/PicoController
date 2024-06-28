from configuration.base_options import BaseOptions

DEFAULT_BUTTON_PIN = "15"


class StripOptions(BaseOptions):
    NAME = "strip"

    def __init__(self):
        super().__init__()

    @property
    def strip_pin(self):
        try:
            pin = self.manager.read_config(self.app_settings_name)["strip"]["pin"]

            if pin == "":
                return DEFAULT_BUTTON_PIN

            return pin
        except KeyError:
            return DEFAULT_BUTTON_PIN

    @property
    def length(self):
        return max(0, int(self.manager.read_config(self.app_settings_name)["strip"]["length"]))

    @length.setter
    def length(self, value: int):
        self.manager.update_config(self.NAME, "length", str(value))

    def empty(self) -> bool:
        return False
