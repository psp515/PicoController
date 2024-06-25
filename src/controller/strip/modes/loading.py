import asyncio

from controller.strip.modes.off import OFF_COLOR
from controller.strip.modes.static import Static

DEFAULT_RUNNING_LEDS = 5
DEFAULT_LOADING_DELAY = 50


class Loading(Static):
    async def _color(self):
        return OFF_COLOR

    async def run(self):
        self.logger.info("Initializing RGB mode.")

        if self._is_strip_inconsistent():
            await self.animate_to_color(OFF_COLOR)

        self.logger.info("Starting RGB mode.")
        while True:
            await self.animate()

    async def animate(self):
        state = await self.state_manager.state()
        data = state.mode_data

        running_leds = self._running_leds(data)
        color = self._deduce_color(state)
        default_brightness = state.brightness

        for i in range(self.strip.length):
            self.strip.neopixel.fill((0, 0, 0))

            for j in range(running_leds-1, -1, -1):
                brightness_factor = 0.2 + (1 - j / (running_leds - 1)) * 0.8
                color.set_brightness(brightness_factor * default_brightness)
                self.strip.neopixel[(i + j) % self.strip.length] = color.rgb()

            self.strip.neopixel.write()
            await asyncio.sleep_ms(DEFAULT_LOADING_DELAY)

    def _running_leds(self, data: {}):
        if "running" in data and isinstance(data["running"], int):
            return data["running"]

        return min(DEFAULT_RUNNING_LEDS, self.strip.length)

    def _is_strip_inconsistent(self):
        for i in range(self.strip.length):
            if self.strip.neopixel[i] != OFF_COLOR.rgb():
                return True

        return False
