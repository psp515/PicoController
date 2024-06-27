import asyncio

from devices.status_beam import StatusBeam
from utils.logger import Logger


HEARTBEAT_DELAY = 11


class Heartbeat:
    def __init__(self):
        self.logger = Logger()
        self.led = StatusBeam()

    async def run(self):

        while True:
            self.logger.debug("Heartbeat.")
            await self.led.blink(1)
            await asyncio.sleep(HEARTBEAT_DELAY)
