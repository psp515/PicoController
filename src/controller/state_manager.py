import json
import asyncio

from configuration.options.mqtt_options import MqttOptions
from utils.extensions.dict_extensions import deep_copy
from utils.logger import Logger


class State:
    def __init__(self, working: bool, brightness: float, mode: int, mode_data: {}):
        self.working = working
        self.brightness = brightness
        self.mode = mode
        self.mode_data = mode_data

    def json(self) -> {}:
        return {
            'brightness': self.brightness,
            'mode': self.mode,
            'working': self.working,
            'mode_data': self.mode_data
        }

    def json_dump(self) -> str:
        return json.dumps(self.json())

    def __eq__(self, other) -> bool:
        if not isinstance(other, State):
            return False
        return (self.working == other.working and
                self.brightness == other.brightness and
                self.mode == other.mode and
                self.mode_data == other.mode_data)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


DEFAULT_STATE = State(False, 1.0, 1, {})
MAX_MODE_ID = 3
MIN_MODE_ID = 0


class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._brightness = 1.0
            self._mode = 1
            self._mode_data = {}
            self._working = False

            self._update_mqtt = False

            self._lock = asyncio.Lock()
            self._logger = Logger()
            self._mqtt_options = MqttOptions()

            self.initialized = True

    async def on(self):
        try:
            await self._lock.acquire()
            self._working = True
            self._update_mqtt = True
        except Exception as e:
            self._logger.error(f"Error when toggling working state. Exception: {e}")
        finally:
            self._lock.release()

    async def off(self):
        try:
            await self._lock.acquire()
            self._working = False
            self._update_mqtt = True
        except Exception as e:
            self._logger.error(f"Error when toggling working state. Exception: {e}")
        finally:
            self._lock.release()

    async def next_mode(self):
        try:
            await self._lock.acquire()
            self._mode = (self._mode + 1) % (MAX_MODE_ID + 1)
            self._update_mqtt = True
        except Exception as e:
            self._logger.error(f"Error when switching mode. Exception: {e}")
        finally:
            self._lock.release()

    async def handle(self, topic: str, payload: str):

        if topic != self._mqtt_options.topic:
            self._logger.debug(f"Received message on topic: {topic}. Expected topic: {self._mqtt_options.topic}")
            return

        self._logger.debug(f"Handling state data: {payload}")
        try:
            await self._lock.acquire()
            data = json.loads(payload)

            if 'working' in data:
                working = data['working']
                self._logger.debug(f"Read Working: {working}")
                if isinstance(working, bool):
                    self._working = working
                else:
                    raise ValueError("Working must be a boolean")

            if not self._working:
                self._logger.info("Controller is not working. Cannot update state.")
                return

            if 'mode' in data:
                mode = data['mode']
                self._logger.debug(f"Read Mode: {mode}")
                if isinstance(mode, int) and MIN_MODE_ID <= mode <= MAX_MODE_ID:
                    self._mode = mode
                else:
                    raise ValueError("Mode must be an integer between 1 and 10")

            if 'brightness' in data:
                brightness = data['brightness']
                self._logger.debug(f"Read Brightness: {brightness}")
                if not isinstance(brightness, float):
                    ValueError("Brightness is not float")

                brightness = round(float(brightness), 2)

                if 0.01 <= brightness <= 1.0:
                    self._brightness = brightness
                else:
                    raise ValueError("Brightness must be a float between 0.01 and 1.0")

            if 'mode_data' in data:
                self._logger.debug(f"Read Mode Data: {data['mode_data']}")
                self._mode_data = data['mode_data']

            if self._mode == 0:
                self._logger.debug("Clearing Mode Data for mode 0.")
                self._mode_data = {}

        except Exception as e:
            self._logger.error(f"Error when handling state data. Exception: {e}")
        finally:
            self._lock.release()

    async def state(self):
        try:
            await self._lock.acquire()
            data = deep_copy(self._mode_data)
            return State(self._working, self._brightness, self._mode, data)
        except Exception as e:
            self._logger.error(f"Error when getting state. Exception: {e}")
        finally:
            self._lock.release()

    async def should_update_mqtt(self):
        try:
            await self._lock.acquire()
            return self._update_mqtt
        except Exception as e:
            self._logger.error(f"Error when updating mqtt. Exception: {e}")
        finally:
            self._update_mqtt = False
            self._lock.release()
