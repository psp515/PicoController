import asyncio

from controller.strip.modes.mode import Mode, DEFAULT_DELAY, START_DELAY


class Rgb(Mode):
    async def run(self):
        self.logger.info("Initializing RGB mode.")
        await self.animate_to_start_colors()

        self.logger.info("Starting RGB mode.")
        while True:
            await self.animate()

    async def animate(self):

        state = await self.state_manager.state()

        for j in range(256):
            for i in range(self.strip.length):
                pixel_index = (i * 256 // self.strip.length + j) & 255
                self.strip.neopixel[i] = self._color_wheel(pixel_index, state.brightness)
            self.strip.neopixel.write()
            await asyncio.sleep_ms(DEFAULT_DELAY)

            if j % 16 == 0:
                state = await self.state_manager.state()

    async def animate_to_start_colors(self):
        steps = 64

        state = await self.state_manager.state()

        for step in range(steps + 1):
            blend_factor = step / steps
            for i in range(self.strip.length):
                current_color = self.strip.neopixel[i]
                start_color = self._color_wheel((i * 256 // self.strip.length) & 255, state.brightness)
                new_color = self._blend_colors(current_color, start_color, blend_factor)
                self.strip.neopixel[i] = new_color
            self.strip.neopixel.write()
            await asyncio.sleep_ms(START_DELAY)

    @staticmethod
    def _blend_colors(color1, color2, blend_factor):
        """Blend two colors together by a given blend factor (0.0 to 1.0)."""
        return (
            int(color1[0] * (1 - blend_factor) + color2[0] * blend_factor),
            int(color1[1] * (1 - blend_factor) + color2[1] * blend_factor),
            int(color1[2] * (1 - blend_factor) + color2[2] * blend_factor)
        )

    @staticmethod
    def _color_wheel(pos, brightness=1.0):
        if pos < 0 or pos > 255:
            return 0, 0, 0

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

        return int(r * brightness), int(g * brightness), int(b * brightness)
