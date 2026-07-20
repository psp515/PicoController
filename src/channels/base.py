class Channel:
    name = "channel"

    def __init__(self, state, logger):
        self.state = state
        self.logger = logger

    async def start(self):
        pass

    async def stop(self):
        pass
