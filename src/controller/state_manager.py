import json


class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._brightness = 0
            self._mode = 0
            self._mode_data = {}
            self._working = False
            self._updated = False

    @property
    def brightness(self):
        return self._brightness

    @property
    def mode(self):
        return self._mode

    @property
    def working(self):
        return self._working

    def updated(self) -> bool:
        return self._updated

    def handle(self, payload: str):
        data = json.loads(payload)

        if 'brightness' in data:
            brightness = data['brightness']
            if isinstance(brightness, float) and 0.01 <= brightness <= 1.0:
                self._brightness = brightness
            else:
                raise ValueError("Brightness must be a float between 0.01 and 1.0")

        if 'mode' in data:
            mode = data['mode']
            if isinstance(mode, int) and 0 <= mode <= 10:
                self._mode = mode
            else:
                raise ValueError("Mode must be an integer between 1 and 10")

        if 'working' in data:
            is_working = data['working']
            if isinstance(is_working, bool):
                self._working = is_working
            else:
                raise ValueError("working must be a boolean")

        if 'mode_data' in data:
            self._mode_data = data['mode_data']

        self._updated = True

    def get_state(self) -> {}:
        return {
            'brightness': self._brightness,
            'mode': self._mode,
            'working': self._working
        }
