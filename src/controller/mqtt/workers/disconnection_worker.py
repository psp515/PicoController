from controller.mqtt.factories.factory import MqttFactory
from controller.interfaces.worker import Worker


class DisconnectionWorker(Worker):
    def __init__(self):
        super().__init__()
        self._factory = MqttFactory()
        self._client = self._factory.create()
        self._outages = 0

    async def run(self):
        self.logger.info("Starting mqtt disconnection worker.")
        try:
            while True:
                await self._client.down.wait()
                self._client.down.clear()
                self.logger.error("Wifi or broker connection is down.")
        except Exception as e:
            self.logger.error(f"Error in disconnection worker: {e}")

