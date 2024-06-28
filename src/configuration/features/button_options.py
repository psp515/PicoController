from configuration.base_options import BaseOptions

DEFAULT_BUTTON_PIN = "14"


class ButtonOptions(BaseOptions):
    def __init__(self):
        super().__init__()

    @property
    def button_pin(self) -> str:
        try:
            pin = self.manager.read_config(self.app_settings_name)["button"]["pin"]

            if pin == "":
                return DEFAULT_BUTTON_PIN

            return pin
        except KeyError:
            return DEFAULT_BUTTON_PIN

    def empty(self) -> bool:
        return False
