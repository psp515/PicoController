import uasyncio

from controller.mqtt.mqtt_client import MqttClient
from controller.worker import Worker


class MqttWorker(Worker):
    def __init__(self):
        super().__init__()
        self._client = MqttClient()

    async def run(self):
        self.logger.info("Starting mqtt worker.")
        while True:
            try:
                self._client.get_message()
                await uasyncio.sleep_ms(100)
            except Exception as e:
                self.logger.error(f"Error in mqtt worker. Exception: {e}")
                self._client.reconnect()
                await uasyncio.sleep(100)
