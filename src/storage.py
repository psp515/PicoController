import asyncio
import json
import os

from defaults import DEFAULTS

CONFIG_FILE = "config.json"
DEV_CONFIG_FILE = "config.dev.json"


def merge(base, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


class Storage:
    def __init__(self, config_file=CONFIG_FILE, dev_config_file=DEV_CONFIG_FILE):
        self._config_file = config_file
        self._dev_config_file = dev_config_file

    def _exists(self, path):
        try:
            os.stat(path)
            return True
        except OSError:
            return False

    def config_file(self):
        if self._exists(self._dev_config_file):
            return self._dev_config_file
        return self._config_file

    def load(self):
        data = json.loads(json.dumps(DEFAULTS))
        try:
            with open(self.config_file()) as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("config root must be a dict")
            merge(data, loaded)
        except (OSError, ValueError):
            self.save(data)
        return data

    def save(self, data, logger=None):
        persisted = {key: value for key, value in data.items() if key != "runtime"}
        path = self.config_file()
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(persisted, f)
        os.rename(tmp, path)
        if logger:
            logger.info("storage", "config saved to {0}", path)

    async def autosave(self, state, logger=None, delay_ms=2000):
        while True:
            await state.changed.wait()
            while state.changed.is_set():
                state.changed.clear()
                await asyncio.sleep_ms(delay_ms)
            self.save(state.data(), logger)
