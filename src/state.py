import asyncio
import time

from storage import merge

VERSION = "2.0.0"

try:
    import binascii
    import machine

    _DEVICE_ID = binascii.hexlify(machine.unique_id()).decode()
except ImportError:
    _DEVICE_ID = "dev"


class BaseState:
    def __init__(self):
        self._started = time.ticks_ms()

    @property
    def device_id(self):
        return _DEVICE_ID

    @property
    def version(self):
        return VERSION

    @property
    def uptime_ms(self):
        return time.ticks_diff(time.ticks_ms(), self._started)

    def info(self):
        return {
            "id": self.device_id,
            "version": self.version,
            "uptime_ms": self.uptime_ms,
        }


class Mode:
    def __init__(self, state):
        self._state = state

    @property
    def current(self):
        return self._state.get("mode", "current", default="off")

    @property
    def brightness(self):
        return self._state.get("mode", "brightness", default=255)

    @property
    def speed(self):
        return self._state.get("mode", "speed", default=10)

    def params(self, name=None):
        if name is None:
            name = self.current
        return self._state.get("modes", name, default={})


class StateManager(BaseState):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._subscribers = []
        self.changed = asyncio.Event()
        self.mode = Mode(self)
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    def __getitem__(self, key):
        return self._data[key]

    def get(self, *keys, default=None):
        node = self._data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def data(self):
        return self._data

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def update(self, patch):
        merge(self._data, patch)
        self.changed.set()
        if self.logger:
            self.logger.info("state", "updated keys {0}", list(patch.keys()))
        for callback in self._subscribers:
            callback(patch)
