from controller.mqtt.factories.factory import MqttFactory
from controller.interfaces.worker import Worker


class ConnectionWorker(Worker):
    def __init__(self):
        super().__init__()
        self._factory = MqttFactory()
        self._client = self._factory.create()
        self._topics = [self._factory.mqtt_options.topic]

    async def run(self):
        self.logger.info("Starting mqtt connection worker.")
        while True:
            await self._client.up.wait()
            self._client.up.clear()
            self.logger.info("Connection established subscribing to topics.")
            for topic in self._topics:
                self.logger.debug(f"Subscribing to topic: {topic}")
                await self._client.subscribe(topic, 0)
