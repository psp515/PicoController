from utils.logger import Logger

from controller.state_manager import StateManager
from devices.strip import Strip


START_DELAY = 2
DEFAULT_DELAY = 4


class Mode:
    def __init__(self):
        self.strip = Strip()
        self.logger = Logger()
        self.state_manager = StateManager()

    async def run(self):
        pass
