import asyncio
from controller.strip.utils.color import Color
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
            updates = await self.check_updates()

            if updates:
                self.logger.debug("Detected updates.")
                await self.update()

            await asyncio.sleep_ms(LOOP_DELAY)

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
        current = tuple(int(initial[i][k] * (1 - step_factor) + target[k] * step_factor) for k in range(3))
        return tuple(max(0, min(255, factor)) for factor in current)

    async def animate_to_color(self, steps: int = 64):
        self.logger.debug(f"Starting animation.")
        initial = [self.strip.neopixel[i] for i in range(self.strip.length)]

        for step in range(steps):
            step_factor = step / (steps - 1)
            for i in range(self.strip.length):
                self.strip.neopixel[i] = self.calculate_animation_color(initial[i], i, step_factor)

            self.strip.neopixel.write()

            updates = await self.check_updates()

            if updates:
                self.logger.debug("Detected updates. Breaking animation.")
                return

            if step % 10 == 0:
                self.logger.debug(f"Step: {step}")
                self.logger.debug(f"Current color: {self.strip.neopixel[0]}")

            await asyncio.sleep_ms(DEFAULT_DELAY)
