import asyncio

from machine import reset

from utils.logger import Logger


class Module:
    def __init__(self, name: str, restart: bool = True):
        self.logger = Logger()
        self.name = name
        self.workers = []
        self.restart = restart

    async def run(self):
        self.logger.info(f"Starting {self.name} workers.")
        tasks = []
        for worker in self.workers:
            task = asyncio.create_task(worker.run())
            tasks.append(task)

        while True:
            for task in tasks:
                if task.done() and self.restart:
                    self.logger.critical(f"Worker {task} has finished. Restarting device.")
                    await asyncio.sleep(1)
                    reset()

            await asyncio.sleep(1)