from machine import reset

from controller.button.button_module import ButtonModule
from controller.mqtt.mqtt_module import MqttModule
from controller.strip.strip_module import StripModule
from utils.heartbeat import Heartbeat
from mode import Mode


class StripController(Mode):
    def __init__(self):
        super().__init__()
        self._modules = [
            MqttModule(),
            ButtonModule(),
            StripModule()
        ]

    async def start(self):
        try:
            self.logger.info('Initializing led controller.')

            for module in self._modules:
                await module.run()

        except Exception as e:
            self.logger.error(f'Error when initializing modules')
            self.logger.debug(e)
            reset()

        self.logger.info('Initializing heartbeat.')
        heartbeat = Heartbeat()
        await heartbeat.run()
