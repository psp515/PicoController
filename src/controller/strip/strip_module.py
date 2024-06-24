from controller.interfaces.module import Module
from controller.strip.workers.strip_worker import StripWorker
from devices.strip import Strip


class StripModule(Module):
    def __init__(self):
        super().__init__("Strip Module")
        self.workers = [StripWorker()]

    async def run(self):
        self.logger.info(f'Initializing {self.name}')

        self.logger.debug("Clearing strip colors.")
        strip = Strip()
        strip.reset()

        await super().run()