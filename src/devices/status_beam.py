from machine import Pin
from asyncio import sleep_ms, Lock

from utils.logger import Logger

DELAY = 100


class StatusBeam:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, 'initialized', False):
            logger = Logger()
            logger.info("Initializing status beam (default onboard led pin).")
            self.beam = Pin("LED", Pin.OUT)
            self.initialized = True
            self.beam.off()
            self.lock = Lock()

    async def blink(self, n: int = 1):
        async with self.lock:
            for _ in range(n):
                self.beam.on()
                await sleep_ms(DELAY)
                self.beam.off()
                await sleep_ms(DELAY)
