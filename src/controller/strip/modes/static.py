import uasyncio

from controller.strip.modes.mode import Mode
from controller.strip.utils.Color import Color, from_hex

DEFAULT_COLOR = (255, 255, 255)


# TODO: Change current_color to dedicated class
class Static(Mode):
    def __init__(self):
        super().__init__()
        self._current_color = None

    async def run(self):
        self.logger.info("Starting static mode.")

        while True:
            new_color = self._color()

            if self._current_color == new_color:
                await uasyncio.sleep_ms(15)
                continue

            self.logger.debug("Color changed.")
            self._current_color = new_color
            await self.animate_to_color(new_color)

    def _color(self):
        new_data = self.state_manager.mode_data
        if "color" in new_data:
            color = new_data["color"]
            color = from_hex(color)
            if not color.is_valid:
                return self._current_color

            return color.rgb()

        r,g,b = 0, 0, 0

        if "r" in new_data and isinstance(new_data["r"], int):
            r = min(255, max(0, new_data["r"]))

        if "g" in new_data and isinstance(new_data["g"], int):
            g = min(255, max(0, new_data["g"]))

        if "b" in new_data and isinstance(new_data["b"], int):
            b = min(255, max(0, new_data["b"]))

        color = Color(r=r, g=g, b=b)
        if color.is_valid:
            return color.rgb()

        return self._include_brightness(DEFAULT_COLOR, self.state_manager.brightness)



    async def animate_to_color(self, target_color, steps=64):
        self.logger.debug(f"Animating to color: {target_color}")
        for step in range(steps):
            for i in range(self.strip.length):
                current_color = self.strip.neopixel[i]
                new_color = [
                    current_color[j] + (target_color[j] - current_color[j]) * step // steps
                    for j in range(3)
                ]
                self.strip.neopixel[i] = tuple(new_color)
            self.strip.neopixel.write()

            if step % 10 == 0 and target_color != self._color():
                # If color changes, break the loop
                break

            if step % 10 == 0:
                self.logger.debug(f"Step: {step}")
                self.logger.debug(f"Current color: {self.strip.neopixel[0]}")

            await uasyncio.sleep_ms(5)

    @staticmethod
    def _include_brightness(color: tuple, brightness: int) -> tuple:
        return tuple(int(c * brightness) for c in color)
