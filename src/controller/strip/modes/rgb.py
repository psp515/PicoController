import asyncio
from time import ticks_ms

from controller.strip.modes.mode import Mode, DEFAULT_DELAY
from controller.strip.utils.color import Color


class Rgb(Mode):

    def __init__(self):
        super().__init__()
        self.blend_factor = 0

    async def run(self):
        self.logger.info("Initializing RGB mode.")

        self.state = await self.state_manager.state()

        i = 0
        while not self._start_finished() and i < 3:
            self.logger.debug(f"Initializing RGB mode. Try: {i}")
            await self.animate_to_color()
            i += 1

        self.logger.info("Starting RGB mode.")
        while True:
            await self.animate()

    def _start_finished(self) -> bool:
        expected = self.color_for_led(0)
        current = self.strip.neopixel[0]

        return expected.rgb() == current

    def color_for_led(self, n: int) -> Color:
        return self._color_wheel((n * 256 // self.strip.length) & 255, self.state.brightness)

    async def animate(self):
        for j in range(256):
            start = ticks_ms()
            for i in range(self.strip.length):
                pixel_index = (i * 256 // self.strip.length + j) & 255
                self.strip.neopixel[i] = self._color_wheel(pixel_index, self.state.brightness).rgb()
            self.strip.neopixel.write()
            await asyncio.sleep_ms(DEFAULT_DELAY)

            if j % 16 == 0:
                self.state = await self.state_manager.state()

            self.logger.debug(f"Time in ms per frame: {ticks_ms() - start}")

    @staticmethod
    def _color_wheel(pos, brightness=1.0) -> Color:
        if pos < 0 or pos > 255:
            return Color(0, 0, 0, 0)

        brightness = max(0.0, min(1.0, brightness))

        if pos < 85:
            r = 255 - pos * 3
            g = pos * 3
            b = 0
        elif pos < 170:
            pos -= 85
            r = 0
            g = 255 - pos * 3
            b = pos * 3
        else:
            pos -= 170
            r = pos * 3
            g = 0
            b = 255 - pos * 3

        return Color(r=r, g=g, b=b, brightness=brightness)
