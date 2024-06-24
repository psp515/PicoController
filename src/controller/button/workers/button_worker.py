import asyncio

from machine import reset

from controller.state_manager import StateManager
from controller.interfaces.worker import Worker
from devices.management_button import ManagementButton


class ButtonWorker(Worker):
    def __init__(self):
        super().__init__()
        self.button = ManagementButton()
        self.state_manager = StateManager()

    async def run(self):
        self.logger.info("Starting button worker.")

        try:
            while True:
                initial = self.button.pressed()
                if initial:
                    self.logger.debug("Button pressed.")
                    count = 0
                    pressed = True
                    while pressed and count < 50:
                        count += 1
                        pressed = self.button.pressed()
                        await asyncio.sleep_ms(100)

                    await self._handle_press(count)

                await asyncio.sleep_ms(50)
        except Exception as e:
            self.logger.debug(f"Error in button worker: {e}")

    async def _handle_press(self, count: int):
        self.logger.debug(f"Button pressed for {count} times.")

        if count < 10:
            self.logger.debug("Toggle leds.")
            await self.state_manager.toggle_working()

        if count < 25:
            return

        if count < 40:
            self.logger.debug("Toggle leds.")
            await asyncio.sleep(1)
            reset()
