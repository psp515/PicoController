from controller.strip.modes.mode import Mode
from controller.strip.utils.color import Color, from_hex


def default_color(brightness: float):
    return Color(brightness=brightness, r=255, g=255, b=255)


class Static(Mode):
    def __init__(self):
        super().__init__()

    def color_for_led(self, n: int) -> Color:
        data = self.state.mode_data

        if "color" not in data and not ("r" in data or "g" in data or "b" in data):
            return default_color(self.state.brightness)

        if "color" in data:
            return from_hex(data["color"], self.state.brightness)

        r, g, b = 0, 0, 0

        if "r" in data and isinstance(data["r"], int):
            r = data["r"]

        if "g" in data and isinstance(data["g"], int):
            g = data["g"]

        if "b" in data and isinstance(data["b"], int):
            b = data["b"]

        return Color(r=r, g=g, b=b, brightness=self.state.brightness)

