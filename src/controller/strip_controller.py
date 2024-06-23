import network
import uasyncio

from configuration.features.mqtt_options import MqttOptions
from configuration.features.wifi_options import WifiOptions
from controller.button.button_worker import ButtonWorker
from controller.mqtt.mqtt_client import MqttClient
from controller.mqtt.mqtt_worker import MqttWorker
from controller.state_manager import StateManager
from controller.strip.strip_worker import StripWorker
from devices.strip import Strip
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
            self._initialize_button()
            self._initialize_strip()
        except Exception as e:
            self.logger.error(f'Error when initializing led controller. Exception: {e}')
            reset()

        await self._heartbeat.run()

    async def _initialize_wifi(self):
        self.logger.info('Initializing wifi connection.')
        options = WifiOptions()
        self._wlan.active(True)
        await uasyncio.sleep_ms(150)

        self._list_netowrks()

        self.logger.debug(f"Trying to connect to: {options.ssid} with password: {options.password}")
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
        self.logger.info('Initializing mqtt observer.')
        self._client.connect()
        uasyncio.create_task(self._worker.run())

    def _initialize_button(self):
        self.logger.info('Initializing button observer.')
        worker = ButtonWorker()
        uasyncio.create_task(worker.run())

    def _initialize_strip(self):
        self.logger.info('Initializing strip controller.')
        manager = StateManager()
        options = MqttOptions()
        self._client.subscribe(options.topic, manager.handle)
        worker = StripWorker()
        uasyncio.create_task(worker.run())

        self.logger.debug("Clearing strip colors.")
        strip = Strip()
        strip.reset()

    def _list_netowrks(self):
        networks = self._wlan.scan()

        for wlan in networks:
            self.logger.debug("SSID: {}".format(wlan[0].decode('utf-8')))
            self.logger.debug("BSSID: {}".format(':'.join(['%02x' % b for b in wlan[1]])))
            self.logger.debug("Channel: {}".format(wlan[2]))
            self.logger.debug("RSSI: {}".format(wlan[3]))
            self.logger.debug("Authmode: {}".format(wlan[4]))
            self.logger.debug("Hidden: {}".format(wlan[5]))
