import network

from controller.interfaces.module import Module
from controller.mqtt.factories.factory import MqttFactory
from controller.mqtt.workers.connection_worker import ConnectionWorker
from controller.mqtt.workers.disconnection_worker import DisconnectionWorker


class MqttModule(Module):
    def __init__(self):
        super().__init__("Mqtt Module")
        self.workers = [ConnectionWorker(),
                        DisconnectionWorker()]

    async def run(self):
        self.logger.info(f'Initializing {self.name}')

        self.logger.info('Initializing Wifi and Mqtt.')
        if self.logger.debug():
            self._list_networks()

        factory = MqttFactory()
        client = factory.create()
        await client.connect()
        await super().run()

    def _list_networks(self):
        wlan = network.WLAN(network.STA_IF)
        networks = wlan.scan()

        self.logger.debug("Networks found: {}".format(len(networks)))
        self.logger.debug("-------------------------------------------")
        for wlan in networks:
            self.logger.debug("SSID: {}".format(wlan[0].decode('utf-8')))
            self.logger.debug("BSSID: {}".format(':'.join(['%02x' % b for b in wlan[1]])))
            self.logger.debug("Channel: {}".format(wlan[2]))
            self.logger.debug("RSSI: {}".format(wlan[3]))
            self.logger.debug("Authmode: {}".format(wlan[4]))
            self.logger.debug("Hidden: {}".format(wlan[5]))
            self.logger.debug("-------------------------------------------")
