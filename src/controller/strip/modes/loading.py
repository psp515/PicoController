import asyncio
from time import ticks_ms

from controller.strip.modes.mode import Mode
from controller.strip.modes.off import OFF_COLOR
from controller.strip.utils.color import Color

DEFAULT_RUNNING_LEDS = 5
DEFAULT_LOADING_DELAY = 20


class Loading(Mode):
    async def run(self):
        self.logger.info("Initializing RGB mode.")

        self.state = await self.state_manager.state()
        if self._is_not_off():
            await self.animate_to_color()

        self.logger.info("Starting RGB mode.")
        while True:
            try:
                self.state = await self.state_manager.state()
                await self.animate()
            except Exception as e:
                self.logger.error(f"Error in RGB mode: {e}")

    def color_for_led(self, n: int) -> Color:
        return OFF_COLOR

    async def animate(self):
        running_leds = self._running_leds(self.state.mode_data)
        color = self.read_color_from_state()

        for i in range(self.strip.length):
            start = ticks_ms()

            self.strip.neopixel.fill((0, 0, 0))

            for j in range(running_leds):
                brightness_factor = 1 - (1 - j / (running_leds - 1)) * 0.8
                color.set_brightness(brightness_factor * self.state.brightness)
                self.strip.neopixel[(i + j) % self.strip.length] = color.rgb()

            self.strip.neopixel.write()
            self.logger.debug(f"Time in ms per frame: {ticks_ms() - start}")

            await asyncio.sleep_ms(DEFAULT_LOADING_DELAY)

    def _running_leds(self, data: {}):
        if "running" in data and isinstance(data["running"], int):
            return data["running"]

        return min(DEFAULT_RUNNING_LEDS, self.strip.length)

    def _is_not_off(self):
        for i in range(self.strip.length):
            if self.strip.neopixel[i] != OFF_COLOR.rgb():
                return True

        return False
