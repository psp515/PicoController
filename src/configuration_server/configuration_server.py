import asyncio
import network
from machine import Pin

from mode import Mode
from utils.heartbeat import Heartbeat
from configuration_server.pages.home import get_home_page, restart_device
from configuration_server.pages.mqtt import get_mqtt_page, post_mqtt_settings
from configuration_server.pages.strip import get_strip_page, post_strip_settings, post_strip_test, post_reset
from configuration_server.pages.wifi import get_wifi_page, post_credentials
from configuration_server.request.request_handler import RequestHandler

DEFAULT_SSID = 'LedController'
DEFAULT_PASSWORD = '123456789'


class ConfigurationServer(Mode):

    def __init__(self):
        super().__init__()
        self.handler = RequestHandler()
        self.heartbeat = Heartbeat()

    async def start(self):
        await self._create_access_point()
        self._initialize_routes()
        await self._run_server()
        await self.heartbeat.run()

    async def _run_server(self):
        self.logger.info("Initializing server.")
        asyncio.create_task(asyncio.start_server(self._handle_client, '0.0.0.0', 80))

    async def _create_access_point(self):
        self.logger.info("Initializing access point.")
        ap = network.WLAN(network.AP_IF)
        ap.config(essid=DEFAULT_SSID, password=DEFAULT_PASSWORD)
        ap.active(True)

        while not ap.active():
            await asyncio.sleep(1)

        self.logger.debug(ap.ifconfig())

    def _initialize_routes(self):
        self.logger.info("Initializing routes.")
        self.handler.map_get('/', get_home_page)
        self.handler.map_post('/restart', restart_device)
        self.handler.map_get('/wifi', get_wifi_page)
        self.handler.map_post('/wifi', post_credentials)
        self.handler.map_get('/mqtt', get_mqtt_page)
        self.handler.map_post('/mqtt', post_mqtt_settings)
        self.handler.map_get('/strip', get_strip_page)
        self.handler.map_post('/strip', post_strip_settings)
        self.handler.map_post('/strip/test', post_strip_test)
        self.handler.map_post('/strip/reset', post_reset)

    async def _handle_client(self, reader, writer):
        self.logger.info("Handling request.")
        await self.handler.handle_request(reader, writer)
        self.logger.info("Request handled.")
