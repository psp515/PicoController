from controller.mqtt.mqtt_client import MqttClient

from controller.worker import Worker


class MqttWorker(Worker):
    def __init__(self):
        super().__init__()
        self._client = MqttClient()

    async def run(self):
        self.logger.info("Starting mqtt worker.")
        while True:
            self.logger.debug("Waiting for message.")
            self._client.get_message()