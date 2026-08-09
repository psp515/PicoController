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
AP_FALLBACK_ATTEMPTS = 3
AP_FALLBACK_MS = 120000
AP_POLL_MS = 1000
DEFAULT_AP_SUFFIX = "-setup"


class WifiChannel(Channel):
    name = "wifi"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._connected = None
        self._ap_active = None
        self._changed = asyncio.Event()
        self._last_good = None
        self._wlan = network.WLAN(network.STA_IF)
        self._ap = network.WLAN(network.AP_IF)

    def _on_change(self, patch):
        self._request_reconnect_if_wifi_changed(patch)

    def _request_reconnect_if_wifi_changed(self, patch):
        if "wifi" in patch:
            self._changed.set()

    def _reconnect_requested(self):
        return self._changed.is_set()

    def _clear_reconnect_request(self):
        self._changed.clear()

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

    async def _run_ap_fallback(self):
        ssid, password = self._ap_credentials()
        self.logger.warning("wifi", "starting setup ap {0}", ssid)
        self._wlan.active(False)
        self._ap.active(True)
        if password:
            self._ap.config(ssid=ssid, password=password)
        else:
            self._ap.config(ssid=ssid, security=0)
        self._publish_ap(True, self._ap.ifconfig()[0])
        waited = 0
        while self._running and waited < AP_FALLBACK_MS and not self._reconnect_requested():
            await asyncio.sleep_ms(AP_POLL_MS)
            waited += AP_POLL_MS
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

    def _should_revert_credentials(self, ssid, password, connected_once, failures):
        return (
            not connected_once
            and failures >= REVERT_ATTEMPTS
            and self._last_good is not None
            and self._last_good != (ssid, password)
        )

    def _revert_to_last_good(self, failures):
        self.logger.warning(
            "wifi", "new credentials failed {0} times, reverting to previous", failures
        )
        self.state.update(
            {"wifi": {"ssid": self._last_good[0], "password": self._last_good[1]}}
        )

    async def _keep_connected(self, ssid, password):
        await self._reset_radio()
        backoff = BACKOFF_MIN_MS
        failures = 0
        connected_once = False
        while self._running and not self._reconnect_requested():
            if self._wlan.isconnected():
                connected_once = True
                failures = 0
                backoff = BACKOFF_MIN_MS
                self._last_good = (ssid, password)
                self._publish(True, self._wlan.ifconfig()[0])
                await asyncio.sleep_ms(MONITOR_MS)
                continue
            self._publish(False, None)
            if await self._connect(ssid, password):
                continue
            failures += 1
            if self._should_revert_credentials(ssid, password, connected_once, failures):
                self._revert_to_last_good(failures)
                return
            if failures >= AP_FALLBACK_ATTEMPTS:
                await self._run_ap_fallback()
                failures = 0
                backoff = BACKOFF_MIN_MS
                continue
            self.logger.debug("wifi", "retry in {0}ms", backoff)
            await asyncio.sleep_ms(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_MS)

    async def start(self):
        self._running = True
        self.state.subscribe(self._on_change)
        while self._running:
            self._clear_reconnect_request()
            ssid = self.state.get("wifi", "ssid", default="")
            password = self.state.get("wifi", "password", default="")
            if not ssid:
                self.logger.warning("wifi", "no ssid configured, starting setup ap")
                self._publish(False, None)
                await self._run_ap_fallback()
                continue
            await self._keep_connected(ssid, password)
            if self._running and self._reconnect_requested():
                self.logger.info("wifi", "config changed, reconnecting")
                self._wlan.disconnect()
                self._publish(False, None)

    async def stop(self):
        self._running = False
        self._changed.set()
        self._wlan.disconnect()
        self._wlan.active(False)
        self._ap.active(False)
        self.logger.info("wifi", "stopped")
