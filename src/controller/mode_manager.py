from controller.state_manager import MAX_MODE_ID, MIN_MODE_ID
from controller.strip.modes.mode import Mode
from controller.strip.modes.static import Static
from controller.strip.modes.static_white import StaticWhite
from controller.strip.modes.rgb import Rgb
from controller.strip.modes.off import Off
from controller.strip.modes.loading import Loading
from utils.logger import Logger


class ModeManager:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ModeManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._logger = Logger()
            self._default_mode = Static
            self._modes = [
                StaticWhite,
                Static,
                Rgb,
                Loading
            ]

            if MAX_MODE_ID + 1 != len(self._modes):
                self._logger.error("Modes are not correctly defined.")
                raise ValueError("Modes are not correctly defined.")

            self.initialized = True

    def get_off_mode(self) -> Mode:
        return Off()

    def get_default_mode(self) -> Mode:
        return self._default_mode()

    def get_mode(self, identification: int) -> Mode:
        if identification < 0 or identification >= len(self._modes):
            return self._default_mode()

        return self._modes[identification]()

    def get_next_mode(self, current: int) -> int:
        return (current + 1) % self.get_modes_count()

    def get_modes_count(self) -> int:
        return len(self._modes)
