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
                    while pressed and count < 25:
                        count += 1
                        pressed = self.button.pressed()
                        await asyncio.sleep_ms(100)

                    self.logger.debug(f"Button pressed for {count} times.")
                    await self._handle_press(count)
                    self.logger.debug(f"Handled pressed action.")

                await asyncio.sleep_ms(20)
        except Exception as e:
            self.logger.debug(f"Error in button worker: {e}")

    async def _handle_press(self, count: int):
        status = await self.state_manager.state()

        if not status.working:
            await self._handle_if_off()
            return

        await self._handle_if_on(count)

        await asyncio.sleep_ms(500)

    async def _handle_if_off(self):
        self.logger.debug("Turning on device.")
        await self.state_manager.on()

    async def _handle_if_on(self, count: int):

        if count < 5:
            self.logger.debug("Toggle mode.")
            await self.state_manager.next_mode()
            return

        if count < 15:
            self.logger.debug("Turning off device.")
            await self.state_manager.off()

        if count <= 25:
            self.logger.debug("Restarting device.")
            await asyncio.sleep_ms(100)
            reset()

        self.logger.debug("Invalid button press count.")