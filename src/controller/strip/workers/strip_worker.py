import asyncio

from controller.mode_manager import ModeManager
from controller.state_manager import StateManager, DEFAULT_STATE, State

from controller.strip.modes.mode import Mode
from controller.interfaces.worker import Worker
from devices.strip import Strip


class StripWorker(Worker):
    def __init__(self):
        super().__init__()
        self._strip = Strip()
        self._state_manager = StateManager()
        self._current_state = DEFAULT_STATE
        self._mode_task = None
        self._mode_manager = ModeManager()

        if self._strip.length < 1:
            raise ValueError("Strip length is less than 1 led.")

        self.logger.debug(f"Current state: {self._current_state.working}")

    async def run(self):
        self.logger.info("Starting strip worker.")

        try:
            while True:
                state = await self._state_manager.state()
                if self._current_state != state:
                    self.logger.debug("New state for controller.")
                    await self._update_state(state)
                    self._current_state = state

                await asyncio.sleep_ms(50)
        except Exception as e:
            self.logger.debug(f"Error in strip worker: {e}")

    async def _update_state(self, state: State):

        if self._turned_on(state):
            self.logger.debug(f"Turning on mode {state.mode}.")
            await self._stop_mode()
            self._start_mode(state.mode)
            return

        if self._turned_off(state):
            self.logger.debug("Turning off mode.")
            await self._stop_mode()
            self._start_off_mode()
            return

        if self._mode_changed(state):
            self.logger.debug(f"Changing mode to {state.mode}.")
            await self._stop_mode()
            self._start_mode(state.mode)
            return

    def _start_mode(self, identification: int):
        self.logger.debug(f"Starting mode: {identification}")
        mode = self._mode_manager.get_mode(identification)
        self._internal_start_mode(mode)

    def _start_off_mode(self):
        self.logger.debug("Starting off mode.")
        off_mode = self._mode_manager.get_off_mode()
        self._internal_start_mode(off_mode)

    def _internal_start_mode(self, mode: Mode):
        self.logger.debug(f"Starting mode: {mode}")
        self._mode_task = asyncio.create_task(mode.run())

    async def _stop_mode(self):
        if self._mode_task is None:
            return

        if self._mode_task.done():
            return

        try:
            self._mode_task.cancel()
            await self._mode_task
        except asyncio.CancelledError:
            self.logger.debug("Animation stopped.")

    def _turned_on(self, state: State):
        return state.working and not self._current_state.working

    def _turned_off(self, state: State):
        return not state.working and self._current_state.working

    def _mode_changed(self, state: State):
        return state.mode != self._current_state.mode
