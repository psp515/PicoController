from utils.logger import Logger


class Mode:

    def __init__(self):
        self.logger = Logger()

    async def start(self):
        self.logger.info("Default mode executed!")
