from logging.logger import Logger


class Worker:
    def __init__(self):
        self.logger = Logger()

    def run(self):
        self.logger.info("Worker is running.")