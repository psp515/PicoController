import asyncio

import channels.webapi as webapi_module
from channels.webapi import WebApiChannel
from logger.logger import Logger
from state import StateManager


class FakeApp:
    def __init__(self):
        self.start_calls = []
        self._shutdown = asyncio.Event()

    async def start_server(self, port=None):
        self.start_calls.append(port)
        self._shutdown.clear()
        await self._shutdown.wait()

    def shutdown(self):
        self._shutdown.set()


def patch_timings(monkeypatch):
    monkeypatch.setattr(webapi_module, "WIFI_POLL_MS", 5)


async def run_scenario(data, body):
    # Constructed inside the running loop, not before `asyncio.run(...)`, so
    # the `asyncio.Event()`s WebApiChannel/FakeApp hold bind to the loop
    # they're actually awaited on.
    state = StateManager(data)
    logger = Logger(state)
    channel = WebApiChannel(state, logger)
    channel._app = FakeApp()
    task = asyncio.create_task(channel.start())
    try:
        await body(channel, state)
    finally:
        await channel.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def test_stays_down_without_network(monkeypatch):
    patch_timings(monkeypatch)

    async def body(channel, state):
        await asyncio.sleep(0.05)
        assert channel._app.start_calls == []

    asyncio.run(run_scenario({}, body))


def test_starts_when_connected(monkeypatch):
    patch_timings(monkeypatch)

    async def body(channel, state):
        state.update({"runtime": {"wifi": {"connected": True}}})
        await asyncio.sleep(0.05)
        assert channel._app.start_calls == [80]

    asyncio.run(run_scenario({}, body))


def test_starts_when_only_ap_active(monkeypatch):
    patch_timings(monkeypatch)

    async def body(channel, state):
        state.update({"runtime": {"wifi": {"ap_active": True}}})
        await asyncio.sleep(0.05)
        assert channel._app.start_calls == [80]

    asyncio.run(run_scenario({}, body))


def test_restart_endpoint_responds_ok_and_schedules_reset(monkeypatch):
    monkeypatch.setattr(webapi_module, "RESTART_DELAY_MS", 5)
    calls = []
    monkeypatch.setattr(webapi_module.machine, "reset", lambda: calls.append(True))

    async def scenario():
        state = StateManager({})
        logger = Logger(state)
        channel = WebApiChannel(state, logger)

        result = await channel._handle_restart(None)
        assert result == {"ok": True}
        assert calls == []

        await asyncio.sleep(0.05)
        assert calls == [True]

    asyncio.run(scenario())


class FakeRequest:
    def __init__(self, method, path):
        self.method = method
        self.path = path


def test_static_routes_serve_files():
    async def scenario():
        state = StateManager({})
        logger = Logger(state)
        channel = WebApiChannel(state, logger)

        for path, content_type in [
            ("/", "text/html"),
            ("/modes", "text/html"),
            ("/config", "text/html"),
            ("/style.css", "text/css"),
            ("/app.js", "application/javascript"),
        ]:
            req = FakeRequest("GET", path)
            handler, _prefix, _subapp = channel._app.find_route(req)
            response = await handler(req)
            assert response.status_code == 200
            assert response.headers["Content-Type"].startswith(content_type)

    asyncio.run(scenario())


def test_wifi_scan_endpoint_sets_request_flag():
    async def scenario():
        state = StateManager({})
        logger = Logger(state)
        channel = WebApiChannel(state, logger)

        req = FakeRequest("POST", "/json/wifi/scan")
        handler, _prefix, _subapp = channel._app.find_route(req)
        result = await handler(req)

        assert result == {"ok": True}
        assert state.get("runtime", "wifi", "scan_requested") is True

    asyncio.run(scenario())


def test_stops_when_disabled_toggle(monkeypatch):
    patch_timings(monkeypatch)

    async def body(channel, state):
        state.update({"runtime": {"wifi": {"connected": True}}})
        await asyncio.sleep(0.05)
        assert len(channel._app.start_calls) == 1
        state.update({"webapi": {"enabled": False}})
        await asyncio.sleep(0.05)
        assert channel._app._shutdown.is_set()

    asyncio.run(run_scenario({}, body))
