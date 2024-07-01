import asyncio
from time import ticks_ms
from controller.strip.utils.color import Color, from_hex
from utils.logger import Logger

from controller.state_manager import StateManager
from devices.strip import Strip

LOOP_DELAY = 1
DEFAULT_DELAY = 1


def default_color(brightness: float):
    return Color(brightness=brightness, r=255, g=255, b=255)


class Mode:
    def __init__(self):
        self.strip = Strip()
        self.logger = Logger()
        self.state_manager = StateManager()

        self.state = None

    async def run(self):
        self.logger.info("Starting mode.")
        while True:
            try:
                updates = await self.check_updates()

                if updates:
                    self.logger.debug("Detected updates.")
                    await self.update()

                await asyncio.sleep_ms(LOOP_DELAY)
            except Exception as e:
                self.logger.error(f"Error in mode: {e}")

    async def check_updates(self) -> bool:
        state = await self.state_manager.state()

        if self.state is None or self.state != state:
            self.state = state
            return True

        return False

    async def update(self):
        self.logger.debug("Updating mode.")
        await self.animate_to_color()

    def color_for_led(self, n: int) -> Color:
        return default_color(self.state.brightness)

    def calculate_animation_color(self, initial: tuple, i: int, step_factor: float) -> tuple:
        target = self.color_for_led(i).rgb()
        current = tuple(int(initial[k] * (1 - step_factor) + target[k] * step_factor) for k in range(3))
        return tuple(max(0, min(255, factor)) for factor in current)

    async def animate_to_color(self, steps: int = 64):
        self.logger.debug(f"Starting animation.")
        initials = [self.strip.neopixel[i] for i in range(self.strip.length)]
        targets = [self.color_for_led(i).rgb() for i in range(self.strip.length)]

        different = False

        for i in range(self.strip.length):
            if initials[i] != targets[i]:
                different = True
                break

        if not different:
            self.logger.debug("No changes in color. Skipping animation.")
            return

        for step in range(steps):
            start = ticks_ms()

            step_factor = step / (steps - 1)
            reverse_factor = (1 - step_factor)
            for i in range(self.strip.length):
                r = int(initials[i][0] * reverse_factor + targets[i][0] * step_factor)
                g = int(initials[i][1] * reverse_factor + targets[i][1] * step_factor)
                b = int(initials[i][2] * reverse_factor + targets[i][2] * step_factor)
                self.strip.neopixel[i] = r, g, b

            self.strip.neopixel.write()

            updates = await self.check_updates()

            if updates:
                self.logger.debug("Detected updates. Breaking animation.")
                return

            if step % 16 == 0:
                self.logger.debug(f"Step: {step}")
                self.logger.debug(f"Current color: {self.strip.neopixel[0]}")

            self.logger.debug(f"Time in ms per frame: {ticks_ms() - start}")

            await asyncio.sleep_ms(DEFAULT_DELAY)

    def read_color_from_state(self) -> Color:
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
