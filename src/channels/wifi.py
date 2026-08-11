import asyncio

import network

from channels.base import Channel

BACKOFF_MIN_MS = 1000
BACKOFF_MAX_MS = 30000
CONNECT_TIMEOUT_MS = 15000
CONNECT_POLL_MS = 500
MONITOR_MS = 2000
RADIO_RESET_MS = 100
AP_FALLBACK_ATTEMPTS = 3
AP_POLL_MS = 1000
SCAN_POLL_MS = 300
DEFAULT_AP_SUFFIX = "-setup"


class WifiChannel(Channel):
    name = "wifi"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._connected = None
        self._ap_active = None
        self._wlan = network.WLAN(network.STA_IF)
        self._ap = network.WLAN(network.AP_IF)

    def _publish(self, connected, ip):
        if connected == self._connected:
            return
        self._connected = connected
        if connected:
            self.logger.info("wifi", "connected ip {0}", ip)
        else:
            self.logger.warning("wifi", "disconnected")
        self.state.update({"runtime": {"wifi": {"connected": connected, "ip": ip}}})

    def _publish_ap(self, active, ip):
        if active == self._ap_active:
            return
        self._ap_active = active
        if active:
            self.logger.warning("wifi", "setup ap up, ip {0}", ip)
        else:
            self.logger.debug("wifi", "setup ap down")
        self.state.update({"runtime": {"wifi": {"ap_active": active, "ap_ip": ip}}})

    def _ap_credentials(self):
        ssid = self.state.get("wifi", "ap_ssid", default="")
        if not ssid:
            name = self.state.get("device", "name", default="PicoController")
            ssid = name + DEFAULT_AP_SUFFIX
        password = self.state.get("wifi", "ap_password", default="")
        return ssid, password

    async def _run_ap_forever(self):
        ssid, password = self._ap_credentials()
        self.logger.warning("wifi", "starting setup ap {0}", ssid)
        self._wlan.active(False)
        self._ap.active(True)
        if password:
            self._ap.config(ssid=ssid, password=password)
        else:
            self._ap.config(ssid=ssid, security=0)
        self._publish_ap(True, self._ap.ifconfig()[0])
        while self._running:
            await asyncio.sleep_ms(AP_POLL_MS)
        self._ap.active(False)
        self._publish_ap(False, None)

    async def _reset_radio(self):
        self.logger.debug("wifi", "resetting radio")
        self._wlan.active(False)
        await asyncio.sleep_ms(RADIO_RESET_MS)

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

    async def _keep_connected(self, ssid, password):
        await self._reset_radio()
        backoff = BACKOFF_MIN_MS
        failures = 0
        while self._running:
            if self._wlan.isconnected():
                failures = 0
                backoff = BACKOFF_MIN_MS
                self._publish(True, self._wlan.ifconfig()[0])
                await asyncio.sleep_ms(MONITOR_MS)
                continue
            self._publish(False, None)
            if await self._connect(ssid, password):
                continue
            failures += 1
            if failures >= AP_FALLBACK_ATTEMPTS:
                self.logger.warning(
                    "wifi", "{0} failed attempts, falling back to setup ap for good", failures
                )
                await self._run_ap_forever()
                return
            self.logger.debug("wifi", "retry in {0}ms", backoff)
            await asyncio.sleep_ms(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_MS)

    def _perform_scan(self):
        try:
            self._wlan.active(True)
            raw = self._wlan.scan()
        except OSError as exc:
            self.logger.warning("wifi", "scan failed: {0}", exc)
            return []
        results = []
        for ssid, _bssid, channel, rssi, security, _hidden in raw:
            if isinstance(ssid, bytes):
                ssid = ssid.decode()
            results.append(
                {"ssid": ssid, "rssi": rssi, "channel": channel, "open": security == 0}
            )
        return results

    async def _scan_service(self):
        while self._running:
            if self.state.get("runtime", "wifi", "scan_requested", default=False):
                self.logger.debug("wifi", "scanning for networks")
                results = self._perform_scan()
                self.state.update(
                    {"runtime": {"wifi": {"scan_requested": False, "scan_results": results}}}
                )
            await asyncio.sleep_ms(SCAN_POLL_MS)

    async def start(self):
        self._running = True
        asyncio.create_task(self._scan_service())
        ssid = self.state.get("wifi", "ssid", default="")
        password = self.state.get("wifi", "password", default="")
        if not ssid:
            self.logger.warning("wifi", "no ssid configured, starting setup ap")
            self._publish(False, None)
            await self._run_ap_forever()
            return
        await self._keep_connected(ssid, password)

    async def stop(self):
        self._running = False
        self._wlan.disconnect()
        self._wlan.active(False)
        self._ap.active(False)
        self.logger.info("wifi", "stopped")
