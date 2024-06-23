import uasyncio
from controller.worker import Worker
from devices.strip import Strip


class StripWorker(Worker):
    def __init__(self):
        super().__init__()
        self._strip = Strip()

        if self._strip.length < 1:
            raise ValueError("Strip length is less than 1 led.")

    async def run(self):
        self.logger.info("Starting strip worker.")

        # TODO

        while True:
            await uasyncio.sleep_ms(10)
