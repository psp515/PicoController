from controller.strip.modes.mode import Mode
from controller.strip.utils.color import Color


class Static(Mode):
    def __init__(self):
        super().__init__()

    def color_for_led(self, n: int) -> Color:
        return self.read_color_from_state()

