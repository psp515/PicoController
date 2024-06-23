import uasyncio

from machine import reset

from controller.state_manager import StateManager
from controller.worker import Worker
from devices.management_button import ManagementButton


class ButtonWorker(Worker):
    def __init__(self):
        super().__init__()
        self.button = ManagementButton()
        self.state_manager = StateManager()

    async def run(self):
        while True:
            initial = self.button.pressed()
            if initial:
                self.logger.debug("Button pressed.")
                count = 0
                pressed = True
                while pressed and count < 50:
                    count += 1
                    pressed = self.button.pressed()
                    await uasyncio.sleep_ms(100)

                await self._handle_press(count)

            await uasyncio.sleep_ms(10)

    async def _handle_press(self, count: int):
        self.logger.debug(f"Button pressed for {count} times.")
        if count < 2:
            return

        if count < 10:
            self.logger.debug("Toogle leds.")
            await self.state_manager.toggle_working()

        if count < 25:
            return

        if count < 40:
            reset()

