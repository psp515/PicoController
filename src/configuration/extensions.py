from configuration.configuration_manager import ConfigurationManager
from configuration.options.mqtt_options import MqttOptions
from configuration.options.strip_options import StripOptions
from configuration.options.wifi_options import WifiOptions


def initialize_configuration():
    manager = ConfigurationManager()
    manager.add_config(WifiOptions.NAME)
    manager.add_config(MqttOptions.NAME)
    manager.add_config(StripOptions.NAME)
