import uasyncio

from controller.strip.modes.mode import Mode

DEFAULT_COLOR = (255, 255, 255)


class Static(Mode):

    async def run(self):
        self.logger.info("Starting static mode.")

        current_color = None

        while True:
            new_color = self._color()

            if current_color == new_color:
                await uasyncio.sleep_ms(50)
                continue

            self.logger.debug("Color changed.")
            current_color = new_color
            self.animate_to_color(current_color)

    def _color(self):
        color = self.state_manager.mode_data.get('color', DEFAULT_COLOR)
        return self._include_brightness(color, self.state_manager.brightness)

    def animate_to_color(self, target_color, steps=64):
        # brightness is already applied to the color
        # we just need to transform from color to color
        # TODO: we might make it more iterative so when color changes again break loop and start new animation
        for step in range(steps):
            for i in range(self.strip.length):
                current_color = self.strip.neopixel[i]
                new_color = [
                    current_color[j] + (target_color[j] - current_color[j]) * step // steps
                    for j in range(3)
                ]
                self.strip.neopixel[i] = tuple(new_color)
            self.strip.neopixel.write()
            uasyncio.sleep_ms(2)

    @staticmethod
    def _include_brightness(color: tuple, brightness: int) -> tuple:
        return tuple(int(c * brightness) for c in color)
