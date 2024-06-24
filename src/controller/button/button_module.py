from controller.button.workers.button_worker import ButtonWorker
from controller.interfaces.module import Module


class ButtonModule(Module):
    def __init__(self):
        super().__init__("Button Module")
        self.workers = [ButtonWorker()]

    async def run(self):
        self.logger.info(f'Initializing {self.name}')
        await super().run()