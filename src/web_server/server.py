import asyncio
import network

from mode import Mode
from web_server.pages.home import get_home_page
from web_server.request.request_handler import RequestHandler

DEFAULT_SSID = 'LedController'
DEFAULT_PASSWORD = '123456789'


class WebServer(Mode):

    def __init__(self):
        super().__init__()
        self.handler = RequestHandler()

    async def start(self):
        await self._create_access_point()
        self._initialize_routes()
        await self._run_server()

    async def _run_server(self):
        self.logger.info("Initializing server.")
        server = await asyncio.start_server(self._handle_client, '0.0.0.0', 80)
        self.logger.info("Server is available.")
        await server.wait_closed()

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

    async def _handle_client(self, reader, writer):
        self.logger.info("Handling request.")
        await self.handler.handle_request(reader, writer)
        self.logger.info("Request handled.")
