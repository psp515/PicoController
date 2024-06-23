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
            if await self.button.wait_for_press():
                count = 0
                pressed = True
                while pressed:
                    count += 1
                    pressed = await self.button.wait_for_press()
                    await uasyncio.sleep_ms(100)

                self._handle_press(count)

            await uasyncio.sleep_ms(100)

    def _handle_press(self, count: int):
        if count < 5:
            return

        if count < 10:
            self.state_manager.toggle_working()

        if count < 25:
            return

        if count < 40:
            reset()
