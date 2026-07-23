import asyncio
import time

from storage import merge

VERSION = "2.0.0"

MODE_RANGES = {"brightness": (1, 100), "speed": (1, 100)}

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
        return self._state.get("mode", "brightness", default=50)

    @property
    def speed(self):
        return self._state.get("mode", "speed", default=10)

    @property
    def on(self):
        return self._state.get("mode", "on", default=True)

    def params(self, name=None):
        if name is None:
            name = self.current
        return self._state.get("modes", name, default={})

    def next_mode(self):
        names = sorted(name for name in self._state["modes"].keys() if name != "off")
        current = self.current
        if current in names:
            next_name = names[(names.index(current) + 1) % len(names)]
        else:
            next_name = names[0]
        self._state.update({"mode": {"current": next_name}})
        return next_name


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
        mode_patch = patch.get("mode")
        if isinstance(mode_patch, dict):
            mode_patch = dict(mode_patch)
            if "current" in mode_patch and mode_patch["current"] not in self._data.get("modes", {}):
                if self.logger:
                    self.logger.warning("state", "unknown mode {0}, keeping current", mode_patch["current"])
                del mode_patch["current"]
            for key, (lo, hi) in MODE_RANGES.items():
                if key not in mode_patch:
                    continue
                value = mode_patch[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    if self.logger:
                        self.logger.warning("state", "invalid {0} {1}, ignoring", key, value)
                    del mode_patch[key]
                elif value < lo or value > hi:
                    mode_patch[key] = max(lo, min(hi, value))
            patch = dict(patch)
            if mode_patch:
                patch["mode"] = mode_patch
            else:
                del patch["mode"]
        if not patch:
            return
        merge(self._data, patch)
        self.changed.set()
        if self.logger:
            self.logger.info("state", "updated keys {0}", list(patch.keys()))
        for callback in self._subscribers:
            callback(patch)
