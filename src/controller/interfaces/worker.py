from utils.logger import Logger


class Worker:
    def __init__(self):
        self.logger = Logger()

    async def run(self):
        self.logger.info("Worker is running.")