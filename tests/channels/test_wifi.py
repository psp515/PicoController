import asyncio

import channels.wifi as wifi_module
from channels.wifi import WifiChannel
from logger.logger import Logger
from state import StateManager


class FakeWlan:
    def __init__(self, good=("home", "pw")):
        self.good = good
        self._connected = False
        self.attempts = []

    def active(self, value=None):
        if value is False:
            self._connected = False

    def connect(self, ssid, password):
        self.attempts.append((ssid, password))
        self._connected = (ssid, password) == self.good

    def isconnected(self):
        return self._connected

    def disconnect(self):
        self._connected = False

    def ifconfig(self):
        return ("192.168.1.10", "255.255.255.0", "192.168.1.1", "192.168.1.1")


def make_channel(data):
    state = StateManager(data)
    logger = Logger(state)
    channel = WifiChannel(state, logger)
    channel._wlan = FakeWlan()
    return channel, state


def patch_timings(monkeypatch):
    monkeypatch.setattr(wifi_module, "RADIO_RESET_MS", 1)
    monkeypatch.setattr(wifi_module, "CONNECT_TIMEOUT_MS", 10)
    monkeypatch.setattr(wifi_module, "CONNECT_POLL_MS", 10)
    monkeypatch.setattr(wifi_module, "MONITOR_MS", 5)
    monkeypatch.setattr(wifi_module, "BACKOFF_MIN_MS", 1)
    monkeypatch.setattr(wifi_module, "BACKOFF_MAX_MS", 5)


async def run_channel_while(channel, body):
    task = asyncio.create_task(channel.start())
    try:
        await body()
    finally:
        await channel.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def test_on_change_reacts_only_to_wifi_patch():
    channel, _ = make_channel({})

    channel._on_change({"mode": {"on": False}})
    assert not channel._changed.is_set()

    channel._on_change({"wifi": {"ssid": "new"}})
    assert channel._changed.is_set()


def test_connects_and_publishes_runtime(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "pw"}})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "connected") is True
        assert state.get("runtime", "wifi", "ip") == "192.168.1.10"

    asyncio.run(run_channel_while(channel, body))


def test_enable_wifi_at_runtime(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "connected") is False
        state.update({"wifi": {"ssid": "home", "password": "pw"}})
        await asyncio.sleep(0.1)
        assert state.get("runtime", "wifi", "connected") is True

    asyncio.run(run_channel_while(channel, body))


def test_reconnects_on_config_change(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "pw"}})

    async def body():
        await asyncio.sleep(0.05)
        channel._wlan.good = ("new", "npw")
        state.update({"wifi": {"ssid": "new", "password": "npw"}})
        await asyncio.sleep(0.1)
        assert ("new", "npw") in channel._wlan.attempts
        assert state.get("runtime", "wifi", "connected") is True

    asyncio.run(run_channel_while(channel, body))


def test_reverts_to_last_good_credentials(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "pw"}})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "connected") is True
        state.update({"wifi": {"ssid": "bad", "password": "bad"}})
        await asyncio.sleep(0.3)
        assert state.get("wifi", "ssid") == "home"
        assert state.get("wifi", "password") == "pw"
        assert state.get("runtime", "wifi", "connected") is True

    asyncio.run(run_channel_while(channel, body))
