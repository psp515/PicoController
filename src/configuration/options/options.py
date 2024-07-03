import json
import asyncio

from utils.extensions.os_extensions import file_exists
from utils.logger import Logger


class BaseOptions:
    def __init__(self, name: str):
        self.__settings = SettingsGuard()
        self._name = name

    async def _read_int(self, key: str, default: int) -> int:
        value = await self.__settings.read(self._name, key, default)
        return int(str(value))

    async def _read_str(self, key: str, default: str) -> str:
        value = await self.__settings.read(self._name, key, default)
        return str(value)

    async def _read_bool(self, key: str, default: str) -> bool:
        value = await self.__settings.read(self._name, key, default)
        return bool(value)

    async def _write_int(self, key: str, value: int):
        await self.__settings.write(self._name, key, value)

    async def _write_str(self, key: str, value: str):
        await self.__settings.write(self._name, key, value)

    async def _write_bool(self, key: str, value: bool):
        await self.__settings.write(self._name, key, value)

    def empty(self) -> bool:
        return True


class SettingsGuard:
    __SETTINGS_FILE = "settings.json"

    def __init__(self):
        self.__access = asyncio.Lock()
        self.__logger = Logger()

        if not file_exists(self.__SETTINGS_FILE):
            with open(self.__SETTINGS_FILE, 'w') as f:
                json.dump({}, f)

    async def read(self, config: str, key: str, default: object) -> object:
        self.__logger.debug(f"Reading {key} from {config}")
        async with self.__access:
            with open(self.__SETTINGS_FILE, 'r') as f:
                settings = json.load(f)

                if config not in settings:
                    return default

                return settings.get(key, default)

    async def write(self, config: str, key: str, value: object):
        self.__logger.debug(f"Writing {key} to {config}")
        async with self.__access:
            with open(self.__SETTINGS_FILE, 'r') as f:
                settings = json.load(f)

            if config not in settings:
                settings[config] = {}

            settings[config][key] = value

            with open(self.__SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)


def _ensure_file_exists(path):
    if not file_exists(path):
        with open(path, 'w') as f:
            json.dump({}, f)


class ConfigurationManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, directory: str = "tmp"):
        if not getattr(self, 'initialized', False):
            self.initialized = True
            self.directory = directory
            if not dir_exists(self.directory):
                os.mkdir(self.directory)
            self.config = {
                "app_settings": 'app_settings.json',
            }

    def add_config(self, name: str):
        """
        Adds a configuration file to the manager.
        :param name: The name to associate with the configuration file.
        :return: self (for chaining)
        """
        self.config[name] = f'{self.directory}/{name}.json'
        _ensure_file_exists(self.config[name])
        return self

    def read_config(self, name: str):
        path = self.config.get(name)
        if path and file_exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def update_config(self, config_name: str, key: str, value: str):
        path = self.config.get(config_name)
        if path and file_exists(path):
            with open(path, 'r') as f:
                config = json.load(f)
            config[key] = value
            with open(path, 'w') as f:
                json.dump(config, f)
