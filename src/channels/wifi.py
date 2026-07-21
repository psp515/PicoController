import asyncio

import network

from channels.base import Channel

BACKOFF_MIN_MS = 1000
BACKOFF_MAX_MS = 30000
CONNECT_TIMEOUT_MS = 15000
MONITOR_MS = 2000
IDLE_MS = 60000


class WifiChannel(Channel):
    name = "wifi"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._connected = None
        self._wlan = network.WLAN(network.STA_IF)

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
            await asyncio.sleep_ms(500)
            waited += 500
        self.logger.debug("wifi", "connect attempt to {0} timed out", ssid)
        return False

    async def start(self):
        self._running = True
        ssid = self.state.get("wifi", "ssid", default="")
        password = self.state.get("wifi", "password", default="")
        if not ssid:
            self.logger.warning("wifi", "no ssid configured, wifi disabled")
            self._publish(False, None)
            while self._running:
                await asyncio.sleep_ms(IDLE_MS)
            return
        backoff = BACKOFF_MIN_MS
        while self._running:
            if self._wlan.isconnected():
                self._publish(True, self._wlan.ifconfig()[0])
                backoff = BACKOFF_MIN_MS
                await asyncio.sleep_ms(MONITOR_MS)
                continue
            self._publish(False, None)
            if await self._connect(ssid, password):
                continue
            self.logger.debug("wifi", "retry in {0}ms", backoff)
            await asyncio.sleep_ms(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_MS)

    async def stop(self):
        self._running = False
        self._wlan.disconnect()
        self._wlan.active(False)
        self.logger.info("wifi", "stopped")
