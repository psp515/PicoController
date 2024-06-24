from configuration.features.mqtt_options import MqttOptions
from mqtt_as import config, MQTTClient
from utils.logger import Logger

from configuration.features.wifi_options import WifiOptions


class MqttFactory:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MqttFactory, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return

        logger = Logger()

        self.mqtt_options = MqttOptions()
        if self.mqtt_options.empty():
            logger.error("MQTT options are not set correctly.")
            raise ValueError("MQTT options are not set correctly.")

        config['user'] = self.mqtt_options.username
        config['password'] = self.mqtt_options.password
        config['server'] = self.mqtt_options.url
        config['ssl'] = True
        config['ssl_params'] = {"server_hostname": self.mqtt_options.url}
        config["queue_len"] = 1

        logger.debug(f"MQTT options: {self.mqtt_options.username}, {self.mqtt_options.password}, {self.mqtt_options.url}")

        self.wifi_options = WifiOptions()
        if self.wifi_options.empty():
            logger.error("Wifi options are not set correctly.")
            raise ValueError("Wifi options are not set correctly.")

        config['ssid'] = self.wifi_options.ssid
        config['wifi_pw'] = self.wifi_options.password

        logger.debug(f"Wifi options: {self.wifi_options.ssid}, {self.wifi_options.password}")

        if logger.is_debug():
            MQTTClient.DEBUG = True

        self._client = MQTTClient(config)
        self.initialized = True

    def create(self) -> MQTTClient:
        return self._client
