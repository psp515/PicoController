import uasyncio
import sys

from controller.state_manager import StateManager, State
from controller.strip.modes.off import Off
from controller.strip.modes.static import Static
from controller.strip.modes.static_white import StaticWhite
from controller.interfaces.worker import Worker
from devices.strip import Strip


class StripWorker(Worker):
    def __init__(self):
        super().__init__()
        self._strip = Strip()
        self._state_manager = StateManager()
        self._last_state = State(False, 1, 0, {})
        self._mode = None

        if self._strip.length < 1:
            raise ValueError("Strip length is less than 1 led.")

        self.logger.debug(f"Current state: {self._last_state.working}")

    async def run(self):
        self.logger.info("Starting strip worker.")

        try:
            while True:
                if self._state_manager.updated():
                    self.logger.debug("New state for controller.")
                    state = await self._state_manager.get_state()
                    await self._update_state()
                    self._last_state = state

                await uasyncio.sleep_ms(40)
        except Exception as e:
            self.logger.debug(f"Error in strip worker: {e}")
            sys.print_exception(exc)

    async def _update_state(self):
        if self.turned_on():
            await self._stop_mode()
            mode_to_start = self._state_manager.mode
            self._start_mode(mode_to_start)
            return

        if self.turned_off():
            await self._stop_mode()
            self._start_mode(0)
            return

        if self.mode_changed():
            await self._stop_mode()
            mode_to_start = self._state_manager.mode
            self._start_mode(mode_to_start)
            return

    def _start_mode(self, mode: int):
        task = None

        if mode == 0:
            task = Off()
        elif mode == 1:
            task = StaticWhite()
        else:
            task = Static()

        self._mode = uasyncio.create_task(task.run())

    async def _stop_mode(self):
        if self._mode is None:
            return

        if self._mode.done():
            return

        try:
            self._mode.cancel()
            await self._mode
        except uasyncio.CancelledError:
            self.logger.debug("Animation stopped.")

    def turned_on(self):
        return self._state_manager.working and not self._last_state.working

    def turned_off(self):
        return not self._state_manager.working and self._last_state.working

    def mode_changed(self):
        return self._state_manager.mode != self._last_state.mode

