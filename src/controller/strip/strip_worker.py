import uasyncio

from configuration.features.mqtt_options import MqttOptions
from controller.mqtt.mqtt_client import MqttClient
from controller.state_manager import StateManager
from controller.strip.modes.off import Off
from controller.worker import Worker
from devices.strip import Strip


class StripWorker(Worker):
    def __init__(self):
        super().__init__()
        self._strip = Strip()
        self._state_manager = StateManager()
        self._last_state = self._state_manager.get_state()
        self._off_mode = Off()
        self._mode = None
        self._mqtt_options = MqttOptions()
        self._mqtt_client = MqttClient()

        if self._strip.length < 1:
            raise ValueError("Strip length is less than 1 led.")

    async def run(self):
        self.logger.info("Starting strip worker.")
        mode = None
        while True:
            if self._state_manager.updated():
                self.logger.debug("New state for controller.")
                state = self._state_manager.get_state()
                self._update_state()
                self._last_state = state

                self._mqtt_client.publish(self._mqtt_options.topic, state.json_dump())

            await uasyncio.sleep_ms(15)

    def _update_state(self):

        if self.turned_on():
            pass

        if self.turned_off():
            pass

        if self.mode_changed():
            pass

    async def _stop_animation(self):
        if self._mode is None:
            return

        try:
            self._mode.cancel()
            await self._mode
        except uasyncio.CancelledError:
            self.logger.debug("Animation stopped.")

    def turned_on(self):
        return self._state_manager.working and not self._last_state.working

    def turned_off(self):
        return not self._state_manager.working and self._last_state.working

    def mode_changed(self):
        return self._state_manager.mode != self._last_state.mode
