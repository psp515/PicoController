from configuration.configuration_manager import ConfigurationManager
from configuration.features.mqtt_options import MqttOptions
from configuration.features.strip_options import StripOptions
from configuration.features.wifi_options import WifiOptions


def initialize_configuration():
    manager = ConfigurationManager()
    manager.add_config(WifiOptions.NAME)
    manager.add_config(MqttOptions.NAME)
    manager.add_config(StripOptions.NAME)
