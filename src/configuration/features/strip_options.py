from configuration.base_options import BaseOptions

DEFAULT_BUTTON_PIN = 15


class StripOptions(BaseOptions):
    NAME = "strip"

    def __init__(self):
        super().__init__()

    @property
    def strip_pin(self) -> int:
        try:
            pin = int(self.manager.read_config(self.app_settings_name)["strip"]["pin"])

            if pin < 0 or pin >= 29:
                return DEFAULT_BUTTON_PIN

            return pin
        except KeyError or ValueError:
            return DEFAULT_BUTTON_PIN

    @property
    def length(self) -> int:
        try:
            return max(0, int(self.manager.read_config(self.NAME)["length"]))
        except ValueError:
            return 0

    @length.setter
    def length(self, value: int):
        self.manager.update_config(self.NAME, "length", str(value))

    def empty(self) -> bool:
        return False
