from configuration.base_options import BaseOptions

DEFAULT_BUTTON_PIN = 14


class ButtonOptions(BaseOptions):
    def __init__(self):
        super().__init__()

    @property
    def button_pin(self) -> int:
        try:
            pin = int(self.manager.read_config(self.app_settings_name)["button"]["pin"])

            if pin < 0 or pin >= 29:
                return DEFAULT_BUTTON_PIN

            return pin
        except KeyError or ValueError:
            return DEFAULT_BUTTON_PIN

    def empty(self) -> bool:
        return False
