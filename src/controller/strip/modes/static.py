import asyncio

from controller.state_manager import State
from controller.strip.modes.mode import Mode, DEFAULT_DELAY
from controller.strip.utils.color import Color, from_hex


def default_color(brightness: float):
    return Color(brightness=brightness, r=255, g=255, b=255)


class Static(Mode):
    def __init__(self):
        super().__init__()
        self._current_color = None

    async def run(self):
        self.logger.info("Starting static mode.")

        while True:
            color = await self._color()

            if self._current_color == color:
                await asyncio.sleep_ms(15)
                continue

            self.logger.debug(f"New color: {color}")
            self._current_color = color
            await self.animate_to_color(color)

    async def _color(self) -> Color:
        try:
            state = await self.state_manager.state()
            return self._deduce_color(state)
        except Exception as e:
            self.logger.error(f"Error when getting color.")
            self.logger.debug(f"Exception: {e}")
            return self._current_color

    def _deduce_color(self, state: State) -> Color:
        data = state.mode_data
        if "color" not in data and not ("r" in data or "g" in data or "b" in data):
            return self._current_color if self._current_color is not None else default_color(state.brightness)

        if "color" in data:
            color = data["color"]
            return from_hex(color, state.brightness)

        r, g, b = 0, 0, 0

        if "r" in data and isinstance(data["r"], int):
            r = data["r"]

        if "g" in data and isinstance(data["g"], int):
            g = data["g"]

        if "b" in data and isinstance(data["b"], int):
            b = data["b"]

        return Color(r=r, g=g, b=b, brightness=state.brightness)

    async def animate_to_color(self, target_color: Color, steps=64):
        self.logger.debug(f"Animating to color: {target_color}")

        for step in range(steps):
            for i in range(self.strip.length):
                current_color = self.strip.neopixel[i]
                new_color = [
                    current_color[j] + (target_color[j] - current_color[j]) * step // steps
                    for j in range(3)
                ]
                #self.logger.debug(f"New color: {new_color}")
                self.strip.neopixel[i] = tuple(new_color)
            self.strip.neopixel.write()

            color = await self._color()
            if step % 10 == 0 and target_color != color:
                break

            if step % 10 == 0:
                self.logger.debug(f"Step: {step}")
                self.logger.debug(f"Current color: {self.strip.neopixel[0]}")

            await asyncio.sleep_ms(DEFAULT_DELAY)
