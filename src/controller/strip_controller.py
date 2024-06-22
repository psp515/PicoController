import network
import uasyncio

from configuration.features.mqtt_options import MqttOptions
from configuration.features.wifi_options import WifiOptions
from controller.mqtt.mqtt_client import MqttClient
from controller.mqtt.mqtt_worker import MqttWorker
from controller.state_manager import StateManager
from controller.strip.strip_worker import StripWorker
from utils.heartbeat import Heartbeat
from machine import reset

from mode import Mode
from utils.network_extensions import get_status_description


class StripController(Mode):
    def __init__(self):
        super().__init__()
        self._heartbeat = Heartbeat()
        self._wlan = network.WLAN(network.STA_IF)
        self._worker = MqttWorker()
        self._client = MqttClient()

    async def start(self):
        try:
            await self._initialize_wifi()
            self._initialize_mqtt()
            self._initialize_strip()
        except Exception as e:
            self.logger.error(f'Error when initializing led controller. Exception: {e}')
            reset()

        await self._heartbeat.run()

    async def _initialize_wifi(self):
        self.logger.info('Initializing wifi connection.')
        options = WifiOptions()
        self._wlan.active(True)
        self._wlan.connect(options.ssid, options.password)

        i = 0
        while not self._wlan.isconnected() and i < 20:
            await uasyncio.sleep(1)
            self.logger.warning(f'Connection status: {get_status_description(self._wlan.status())}')
            i += 1

        if not self._wlan.isconnected():
            self.logger.error('Failed to connect to wifi.')
            raise Exception('Failed to connect to wifi.')

        self.logger.info('Connected to wifi.')
        self.logger.debug(f'IP address: {self._wlan.ifconfig()[0]}')

    def _initialize_mqtt(self):
        self._client.connect()
        uasyncio.create_task(self._worker.run())

    def _initialize_strip(self):
        manager = StateManager()
        options = MqttOptions()
        self._client.subscribe(options.topic, manager.handle)
        worker = StripWorker()
        uasyncio.create_task(worker.run())