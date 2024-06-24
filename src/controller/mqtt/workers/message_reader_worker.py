from controller.interfaces.worker import Worker
from controller.mqtt.factories.factory import MqttFactory
from controller.state_manager import StateManager


class MessageReaderWorker(Worker):
    def __init__(self):
        super().__init__()
        self._factory = MqttFactory()
        self._client = self._factory.create()
        self._state_manager = StateManager()

    async def run(self):
        self.logger.info("Starting message reader worker.")

        try:
            async for topic, payload, retained in self._client.queue:
                topic = topic.decode('utf-8')
                payload = payload.decode('utf-8')
                self.logger.debug(f"Received on topic: {topic}")
                self.logger.debug(f"Retained: {retained}")
                self.logger.debug(f"Payload: {payload}")
                await self._state_manager.handle(topic, payload)
        except Exception as e:
            self.logger.debug(f"Error in message reader worker: {e}")
