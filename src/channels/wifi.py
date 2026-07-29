import asyncio

import network

from channels.base import Channel

BACKOFF_MIN_MS = 1000
BACKOFF_MAX_MS = 30000
CONNECT_TIMEOUT_MS = 15000
CONNECT_POLL_MS = 500
MONITOR_MS = 2000
RADIO_RESET_MS = 100
REVERT_ATTEMPTS = 3


class WifiChannel(Channel):
    name = "wifi"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._connected = None
        self._changed = asyncio.Event()
        self._last_good = None
        self._wlan = network.WLAN(network.STA_IF)

    def _on_change(self, patch):
        if "wifi" in patch:
            self._changed.set()

    def _publish(self, connected, ip):
        if connected == self._connected:
            return
        self._connected = connected
        if connected:
            self.logger.info("wifi", "connected ip {0}", ip)
        else:
            self.logger.warning("wifi", "disconnected")
        self.state.update({"runtime": {"wifi": {"connected": connected, "ip": ip}}})

    async def _connect(self, ssid, password):
        self.logger.debug("wifi", "connecting to {0}", ssid)
        self._wlan.active(True)
        self._wlan.connect(ssid, password)
        waited = 0
        while waited < CONNECT_TIMEOUT_MS:
            if self._wlan.isconnected():
                return True
            await asyncio.sleep_ms(CONNECT_POLL_MS)
            waited += CONNECT_POLL_MS
        self.logger.debug("wifi", "connect attempt to {0} timed out", ssid)
        return False

    async def _run(self, ssid, password):
        self.logger.debug("wifi", "resetting radio")
        self._wlan.active(False)
        await asyncio.sleep_ms(RADIO_RESET_MS)
        backoff = BACKOFF_MIN_MS
        failures = 0
        connected_once = False
        while self._running and not self._changed.is_set():
            if self._wlan.isconnected():
                connected_once = True
                failures = 0
                self._last_good = (ssid, password)
                self._publish(True, self._wlan.ifconfig()[0])
                backoff = BACKOFF_MIN_MS
                await asyncio.sleep_ms(MONITOR_MS)
                continue
            self._publish(False, None)
            if await self._connect(ssid, password):
                continue
            failures += 1
            if (
                not connected_once
                and failures >= REVERT_ATTEMPTS
                and self._last_good
                and self._last_good != (ssid, password)
            ):
                self.logger.warning(
                    "wifi", "new credentials failed {0} times, reverting to previous", failures
                )
                self.state.update(
                    {"wifi": {"ssid": self._last_good[0], "password": self._last_good[1]}}
                )
                return
            self.logger.debug("wifi", "retry in {0}ms", backoff)
            await asyncio.sleep_ms(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_MS)

    async def start(self):
        self._running = True
        self.state.subscribe(self._on_change)
        while self._running:
            self._changed.clear()
            ssid = self.state.get("wifi", "ssid", default="")
            password = self.state.get("wifi", "password", default="")
            if not ssid:
                self.logger.warning("wifi", "no ssid configured, wifi disabled")
                self._publish(False, None)
                await self._changed.wait()
                continue
            await self._run(ssid, password)
            if self._running and self._changed.is_set():
                self.logger.info("wifi", "config changed, reconnecting")
                self._wlan.disconnect()
                self._publish(False, None)

    async def stop(self):
        self._running = False
        self._changed.set()
        self._wlan.disconnect()
        self._wlan.active(False)
        self.logger.info("wifi", "stopped")
