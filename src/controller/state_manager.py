import json
import uasyncio

from logging.logger import Logger


class State:
    def __init__(self, working, brightness, mode, mode_data):
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


class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True

            self._brightness = 1.0
            self._mode = 0
            self._mode_data = {}
            self._working = False

            self._updated = False
            self._lock = uasyncio.Lock()
            self._logger = Logger()

    @property
    def brightness(self) -> float:
        return self._brightness

    @property
    def mode(self) -> int:
        """
        1 - white
        2 - colour
        3 - rgb
        4 - storm
        :return: Mode number
        """
        return self._mode

    @property
    def working(self) -> bool:
        return self._working

    @property
    def mode_data(self) -> {}:
        return self._mode_data

    def toggle_working(self):
        self._lock.acquire()
        try:
            self._working = True if not self._working else False
            self._updated = True
        finally:
            self._lock.release()

    def updated(self) -> bool:
        return self._updated

    def handle(self, payload: str):
        self._lock.acquire()
        try:
            data = json.loads(payload)

            if 'working' in data:
                working = data['working']
                if isinstance(working, bool) and bool(working) != self._working:
                    self._working = working
                    self._updated = True
                else:
                    raise ValueError("working must be a boolean")

            if not self._working:
                self._logger.info("Controller is not working. Cannot update state.")
                return

            if 'brightness' in data:
                brightness = data['brightness']
                if not isinstance(brightness, float):
                    ValueError("Brightness is not float")

                brightness = round(float(brightness), 2)

                if 0.01 <= brightness <= 1.0 and brightness != self._brightness:
                    self._brightness = brightness
                    self._updated = True
                else:
                    raise ValueError("Brightness must be a float between 0.01 and 1.0")

            if 'mode' in data:
                mode = data['mode']
                if isinstance(mode, int) and 1 <= mode <= 4 and int(mode) != self._mode:
                    self._mode = mode
                    self._updated = True
                else:
                    raise ValueError("Mode must be an integer between 1 and 10")

            if 'mode_data' in data:
                self._mode_data = data['mode_data']

            if self._mode == 0:
                self._mode_data = {}

        except Exception as e:
            self._logger.error(f"Error when handling state data. Exception: {e}")
        finally:
            self._lock.release()

    def get_state(self):
        self._lock.acquire()
        try:
            self._updated = False
            return State(self._working, self._brightness, self._mode, self._mode_data)
        finally:
            self._lock.release()
