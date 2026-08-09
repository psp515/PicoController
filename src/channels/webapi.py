import asyncio
import json

import machine
from microdot import Microdot

from channels.base import Channel
from webui.webui import register_ui_routes

WIFI_POLL_MS = 500
PORT = 80
RESTART_DELAY_MS = 300


class WebApiChannel(Channel):
    name = "webapi"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._app = Microdot()
        self._config_changed = asyncio.Event()
        self._routes()
        register_ui_routes(self._app)

    def _enabled(self):
        return self.state.get("webapi", "enabled", default=True)

    def _network_available(self):
        return bool(
            self.state.get("runtime", "wifi", "connected")
            or self.state.get("runtime", "wifi", "ap_active")
        )

    def _on_change(self, patch):
        self._shutdown_server_if_webapi_disabled(patch)

    def _shutdown_server_if_webapi_disabled(self, patch):
        if "webapi" not in patch:
            return
        self._config_changed.set()
        if not self._enabled():
            self._app.shutdown()

    async def _wait_for_webapi_config_change(self):
        await self._config_changed.wait()

    async def _delayed_restart(self):
        await asyncio.sleep_ms(RESTART_DELAY_MS)
        machine.reset()

    async def _handle_restart(self, request):
        self.logger.warning("webapi", "restart requested")
        asyncio.create_task(self._delayed_restart())
        return {"ok": True}

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

        @app.post("/json/restart")
        async def restart(request):
            return await self._handle_restart(request)

        @app.post("/json/wifi/scan")
        async def wifi_scan(request):
            state.update({"runtime": {"wifi": {"scan_requested": True}}})
            return {"ok": True}

    async def start(self):
        self._running = True
        self.state.subscribe(self._on_change)
        while self._running:
            self._config_changed.clear()
            if not self._enabled():
                self.logger.info("webapi", "disabled, waiting for config change")
                await self._wait_for_webapi_config_change()
                continue
            while self._running and self._enabled() and not self._network_available():
                await asyncio.sleep_ms(WIFI_POLL_MS)
            if not self._running or not self._enabled():
                continue
            self.logger.info("webapi", "listening on port {0}", PORT)
            await self._app.start_server(port=PORT)
            self.logger.info("webapi", "server stopped")

    async def stop(self):
        self._running = False
        self._config_changed.set()
        self._app.shutdown()
        self.logger.info("webapi", "stopped")
