import asyncio

from controller.interfaces.worker import Worker
from controller.mqtt.factories.factory import MqttFactory
from controller.state_manager import StateManager


class StateUpdaterWorker(Worker):
    def __init__(self):
        super().__init__()
        self._factory = MqttFactory()
        self._client = self._factory.create()
        self._state_manager = StateManager()
        self._state_topic = self._factory.mqtt_options.topic

    async def run(self):
        self.logger.info("Starting state updater worker.")

        while True:
            should_update = await self._state_manager.should_update_mqtt()

            if should_update:
                state = await self._state_manager.state()
                await self._client.publish(self._state_topic, state.json_dump())

            await asyncio.sleep(0.1)
