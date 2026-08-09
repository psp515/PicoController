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
        self.scan_results = [
            (b"Home", b"\x00" * 6, 6, -50, 3, False),
            (b"Neighbor", b"\x01" * 6, 11, -80, 0, False),
        ]

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

    def scan(self):
        return self.scan_results


class FakeAp:
    def __init__(self):
        self._active = False
        self.active_calls = []
        self.configs = []

    def active(self, value=None):
        if value is None:
            return self._active
        self._active = value
        self.active_calls.append(value)

    def config(self, **kwargs):
        self.configs.append(kwargs)

    def ifconfig(self):
        return ("192.168.4.1", "255.255.255.0", "192.168.4.1", "192.168.4.1")


def make_channel(data):
    state = StateManager(data)
    logger = Logger(state)
    channel = WifiChannel(state, logger)
    channel._wlan = FakeWlan()
    channel._ap = FakeAp()
    return channel, state


def patch_timings(monkeypatch):
    monkeypatch.setattr(wifi_module, "RADIO_RESET_MS", 1)
    monkeypatch.setattr(wifi_module, "CONNECT_TIMEOUT_MS", 10)
    monkeypatch.setattr(wifi_module, "CONNECT_POLL_MS", 10)
    monkeypatch.setattr(wifi_module, "MONITOR_MS", 5)
    monkeypatch.setattr(wifi_module, "BACKOFF_MIN_MS", 1)
    monkeypatch.setattr(wifi_module, "BACKOFF_MAX_MS", 5)
    monkeypatch.setattr(wifi_module, "AP_POLL_MS", 5)
    monkeypatch.setattr(wifi_module, "SCAN_POLL_MS", 5)


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


def test_connects_and_publishes_runtime(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "pw"}})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "connected") is True
        assert state.get("runtime", "wifi", "ip") == "192.168.1.10"

    asyncio.run(run_channel_while(channel, body))


def test_wifi_config_change_has_no_effect_until_restart(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "ap_active") is True

        channel._wlan.good = ("home", "pw")
        state.update({"wifi": {"ssid": "home", "password": "pw"}})
        await asyncio.sleep(0.1)

        assert channel._wlan.attempts == []
        assert state.get("runtime", "wifi", "connected") is not True
        assert state.get("runtime", "wifi", "ap_active") is True

    asyncio.run(run_channel_while(channel, body))


def test_no_ssid_starts_ap_immediately(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"device": {"name": "Pico"}})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "ap_active") is True
        assert state.get("runtime", "wifi", "ap_ip") == "192.168.4.1"
        assert channel._ap.configs[-1]["ssid"] == "Pico-setup"

    asyncio.run(run_channel_while(channel, body))


def test_ap_fallback_after_repeated_failures(monkeypatch):
    patch_timings(monkeypatch)
    monkeypatch.setattr(wifi_module, "AP_FALLBACK_ATTEMPTS", 2)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "wrong"}})

    async def body():
        await asyncio.sleep(0.15)
        assert state.get("runtime", "wifi", "ap_active") is True
        assert len(channel._wlan.attempts) >= 2

    asyncio.run(run_channel_while(channel, body))


def test_ap_fallback_stays_up_forever_no_auto_retry(monkeypatch):
    patch_timings(monkeypatch)
    monkeypatch.setattr(wifi_module, "AP_FALLBACK_ATTEMPTS", 1)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "wrong"}})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "ap_active") is True
        attempts_at_ap = len(channel._wlan.attempts)

        # Even if the network becomes reachable, nothing retries on its own.
        channel._wlan.good = ("home", "wrong")
        await asyncio.sleep(0.1)

        assert state.get("runtime", "wifi", "ap_active") is True
        assert state.get("runtime", "wifi", "connected") is not True
        assert len(channel._wlan.attempts) == attempts_at_ap

    asyncio.run(run_channel_while(channel, body))


def test_reconnects_with_same_credentials_after_drop(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "pw"}})

    async def body():
        await asyncio.sleep(0.05)
        assert state.get("runtime", "wifi", "connected") is True

        channel._wlan._connected = False
        await asyncio.sleep(0.1)
        assert state.get("runtime", "wifi", "connected") is True

    asyncio.run(run_channel_while(channel, body))


def test_scan_request_populates_results(monkeypatch):
    patch_timings(monkeypatch)
    channel, state = make_channel({"wifi": {"ssid": "home", "password": "pw"}})

    async def body():
        await asyncio.sleep(0.05)
        state.update({"runtime": {"wifi": {"scan_requested": True}}})
        await asyncio.sleep(0.05)

        assert state.get("runtime", "wifi", "scan_requested") is False
        results = state.get("runtime", "wifi", "scan_results")
        assert results == [
            {"ssid": "Home", "rssi": -50, "channel": 6, "open": False},
            {"ssid": "Neighbor", "rssi": -80, "channel": 11, "open": True},
        ]

    asyncio.run(run_channel_while(channel, body))
