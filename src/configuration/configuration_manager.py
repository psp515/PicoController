import json
import os

from utils.extensions.os_extensions import dir_exists, file_exists


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
