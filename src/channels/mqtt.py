import asyncio
import json

from mqtt_as import MQTTClient, config as mqtt_config

from channels.base import Channel

IDLE_MS = 60000
WIFI_POLL_MS = 500
RETRY_MS = 5000


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
        cfg["client_id"] = self.state.device_id.encode()
        cfg["server"] = self.state.get("mqtt", "server")
        cfg["port"] = self.state.get("mqtt", "port", default=1883)
        cfg["user"] = self.state.get("mqtt", "user", default="")
        cfg["password"] = self.state.get("mqtt", "password", default="")
        cfg["ssid"] = self.state.get("wifi", "ssid", default="")
        cfg["wifi_pw"] = self.state.get("wifi", "password", default="")
        cfg["will"] = (self._base + "/status", "offline", True, 0)
        cfg["queue_len"] = 4
        return MQTTClient(cfg)

    async def _handle_up(self):
        while self._running:
            await self._client.up.wait()
            self._client.up.clear()
            try:
                await self._client.subscribe(self._base + "/set", 0)
                await self._client.publish(self._base + "/status", "online", True, 0)
            except OSError:
                self.logger.warning("mqtt", "failed to subscribe/announce on {0}", self._base)
                continue
            self.logger.info("mqtt", "session up, subscribed {0}/set", self._base)
            self._changed.set()

    async def _handle_messages(self):
        async for topic, msg, retained in self._client.queue:
            try:
                patch = json.loads(msg)
            except ValueError:
                self.logger.warning("mqtt", "invalid json payload on {0}", topic)
                continue
            if isinstance(patch, dict):
                self.state.update(patch)
            else:
                self.logger.warning("mqtt", "payload on {0} is not an object", topic)

    async def _publish_state(self):
        while self._running:
            await self._changed.wait()
            self._changed.clear()
            payload = json.dumps(
                {
                    "mode": self.state.get("mode"),
                    "leds": self.state.get("leds"),
                }
            )
            try:
                await self._client.publish(self._base + "/state", payload, True, 0)
            except OSError:
                self.logger.warning("mqtt", "publish to {0}/state failed", self._base)

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
        self._client = self._build_client()
        while self._running:
            try:
                await self._client.connect()
                break
            except OSError:
                self.logger.warning("mqtt", "connect to {0} failed, retry in {1}ms", server, RETRY_MS)
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
