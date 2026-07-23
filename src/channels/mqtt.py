import asyncio
import gc
import json

import ntptime
from mqtt_as import MQTTClient, config as mqtt_config

from channels.base import Channel

IDLE_MS = 60000
WIFI_POLL_MS = 500
RETRY_MS = 15000
NTP_RETRY_MS = 2000

ALLOWED_SET_KEYS = {
    "mode": {"current", "brightness", "speed", "on"},
    "leds": {"count"},
}


class MqttChannel(Channel):
    name = "mqtt"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._client = None
        self._tasks = []
        self._base = "picocontroller"
        self._changed = asyncio.Event()

    def _on_change(self, patch):
        self._changed.set()

    def _build_client(self):
        cfg = dict(mqtt_config)
        server = self.state.get("mqtt", "server")
        cfg["client_id"] = self.state.device_id.encode()
        cfg["server"] = server
        cfg["port"] = self.state.get("mqtt", "port", default=1883)
        cfg["user"] = self.state.get("mqtt", "user", default="")
        cfg["password"] = self.state.get("mqtt", "password", default="")
        cfg["ssid"] = self.state.get("wifi", "ssid", default="")
        cfg["wifi_pw"] = self.state.get("wifi", "password", default="")
        cfg["will"] = (self._base + "/state/online", "offline", True, 0)
        cfg["queue_len"] = 4
        ssl_enabled = self.state.get("mqtt", "ssl", default=False)
        cfg["ssl"] = ssl_enabled
        if ssl_enabled:
            ssl_params = dict(self.state.get("mqtt", "ssl_params", default={}))
            ssl_params.setdefault("server_hostname", server)
            cfg["ssl_params"] = ssl_params
        return MQTTClient(cfg)

    def _sync_time(self):
        ntptime.host = self.state.get("mqtt", "ntp_host", default="pool.ntp.org")
        try:
            ntptime.settime()
            self.logger.info("mqtt", "time synced via {0}", ntptime.host)
            return True
        except OSError as e:
            self.logger.warning("mqtt", "ntp sync via {0} failed: {1}", ntptime.host, e)
            return False

    async def _handle_up(self):
        while self._running:
            await self._client.up.wait()
            self._client.up.clear()
            try:
                await self._client.subscribe(self._base + "/state/update", 0)
                await self._client.publish(self._base + "/state/online", "online", True, 0)
            except OSError as e:
                self.logger.warning("mqtt", "failed to subscribe/announce on {0}: {1}", self._base, e)
                continue
            self.logger.info("mqtt", "session up, subscribed {0}/state/update", self._base)
            self._changed.set()

    def _filter_set_patch(self, patch):
        allowed = {}
        for key, fields in patch.items():
            if key not in ALLOWED_SET_KEYS or not isinstance(fields, dict):
                continue
            filtered_fields = {k: v for k, v in fields.items() if k in ALLOWED_SET_KEYS[key]}
            if filtered_fields:
                allowed[key] = filtered_fields
        return allowed

    async def _handle_messages(self):
        async for topic, msg, retained in self._client.queue:
            try:
                patch = json.loads(msg)
            except ValueError:
                self.logger.warning("mqtt", "invalid json payload on {0}", topic)
                continue
            if not isinstance(patch, dict):
                self.logger.warning("mqtt", "payload on {0} is not an object", topic)
                continue
            allowed = self._filter_set_patch(patch)
            if allowed:
                self.state.update(allowed)
            else:
                self.logger.warning("mqtt", "payload on {0} had no allowed keys", topic)

    async def _publish_state(self):
        while self._running:
            await self._changed.wait()
            self._changed.clear()
            payload = json.dumps(
                {
                    "mode": self.state.get("mode"),
                    "leds": {"count": self.state.get("leds", "count")},
                }
            )
            try:
                await self._client.publish(self._base + "/state/full", payload, True, 0)
            except OSError as e:
                self.logger.warning("mqtt", "publish to {0}/state/full failed: {1}", self._base, e)

    async def start(self):
        self._running = True
        server = self.state.get("mqtt", "server", default="")
        if not server:
            self.logger.info("mqtt", "no server configured, mqtt disabled")
            while self._running:
                await asyncio.sleep_ms(IDLE_MS)
            return
        while self._running and not self.state.get("runtime", "wifi", "connected"):
            await asyncio.sleep_ms(WIFI_POLL_MS)
        if not self._running:
            return
        self._base = self.state.get("mqtt", "base_topic", default="picocontroller")
        if self.state.get("mqtt", "ssl", default=False):
            while self._running and not self._sync_time():
                await asyncio.sleep_ms(NTP_RETRY_MS)
            if not self._running:
                return
        self._client = self._build_client()
        while self._running:
            gc.collect()
            self.logger.debug("mqtt", "free memory before connect: {0}", gc.mem_free())
            try:
                await self._client.connect()
                break
            except OSError as e:
                self.logger.warning("mqtt", "connect to {0} failed, retry in {1}ms: {2}", server, RETRY_MS, e)
                await asyncio.sleep_ms(RETRY_MS)
        if not self._running:
            return
        self.logger.info("mqtt", "connected to {0}:{1}", server, self.state.get("mqtt", "port", default=1883))
        self.state.subscribe(self._on_change)
        self._tasks = [
            asyncio.create_task(self._handle_up()),
            asyncio.create_task(self._handle_messages()),
            asyncio.create_task(self._publish_state()),
        ]
        while self._running:
            await asyncio.sleep_ms(IDLE_MS)

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks = []
        if self._client:
            self._client.close()
            self._client = None
        self.logger.info("mqtt", "stopped")
