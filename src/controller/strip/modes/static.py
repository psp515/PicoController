import uasyncio

from controller.strip.modes.mode import Mode
from controller.strip.utils.Color import Color, from_hex

DEFAULT_COLOR = Color(1.0, 255, 255, 255)


class Static(Mode):
    def __init__(self):
        super().__init__()
        self._current_color = DEFAULT_COLOR

    async def run(self):
        self.logger.info("Starting static mode.")

        while True:
            color = await self._color()

            if self._current_color == color:
                await uasyncio.sleep_ms(15)
                continue

            self.logger.debug("Color changed.")
            self._current_color = color
            await self.animate_to_color(color)

    async def _color(self) -> Color:
        try:
            state = await self.state_manager.state()
            data = state.mode_data
            if "color" in data:
                color = data["color"]
                return from_hex(color, state.brightness)

            if not ("r" in data or "g" in data or "b" in data):
                return self._current_color

            r, g, b = 0, 0, 0

            if "r" in data and isinstance(data["r"], int):
                r = data["r"]

            if "g" in data and isinstance(data["g"], int):
                g = data["g"]

            if "b" in data and isinstance(data["b"], int):
                b = data["b"]

            return Color(r=r, g=g, b=b, brightness=state.brightness)
        except Exception as e:
            self.logger.error(f"Error when getting color.")
            self.logger.debug(f"Exception: {e}")
            return self._current_color

    async def animate_to_color(self, target_color: Color, steps=64):
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

            color = await self._color()
            if step % 10 == 0 and target_color != color:
                break

            if step % 10 == 0:
                self.logger.debug(f"Step: {step}")
                self.logger.debug(f"Current color: {self.strip.neopixel[0]}")

            await uasyncio.sleep_ms(5)

    @staticmethod
    def _include_brightness(color: tuple, brightness: int) -> tuple:
        return tuple(int(c * brightness) for c in color)
