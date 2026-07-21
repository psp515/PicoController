import asyncio
import json

from microdot import Microdot

from channels.base import Channel

WIFI_POLL_MS = 500
PORT = 80


class WebApiChannel(Channel):
    name = "webapi"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._app = Microdot()
        self._routes()

    def _routes(self):
        app = self._app
        state = self.state
        logger = self.logger

        @app.get("/json/state")
        async def get_state(request):
            return state.data()

        @app.post("/json/state")
        async def post_state(request):
            try:
                patch = json.loads(request.body)
            except ValueError:
                logger.warning("webapi", "invalid json in POST /json/state")
                return {"error": "invalid json"}, 400
            if not isinstance(patch, dict):
                logger.warning("webapi", "POST /json/state body is not an object")
                return {"error": "invalid json"}, 400
            state.update(patch)
            return {"ok": True}

        @app.get("/info")
        async def info(request):
            return state.info()

    async def start(self):
        while not self.state.get("runtime", "wifi", "connected"):
            await asyncio.sleep_ms(WIFI_POLL_MS)
        self.logger.info("webapi", "listening on port {0}", PORT)
        await self._app.start_server(port=PORT)

    async def stop(self):
        self._app.shutdown()
        self.logger.info("webapi", "stopped")
