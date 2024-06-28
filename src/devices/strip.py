import neopixel

from machine import Pin

from configuration.features.strip_options import StripOptions
from utils.logger import Logger

MAX_PIXELS = 300


class Strip:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            logger = Logger()
            options = StripOptions()
            logger.info(f"Initializing strip with pin {options.strip_pin} and length {options.length}")
            self.pin = Pin(options.strip_pin, Pin.OUT)
            self._initialized = True
            self.length = options.length
            self._neopixel = neopixel.NeoPixel(self.pin, self.length)

    @property
    def neopixel(self):
        return self._neopixel

    def test_length(self, length: int):
        if length > MAX_PIXELS:
            length = MAX_PIXELS

        self.reset()

        test_pixel = neopixel.NeoPixel(self.pin, length)
        for i in range(length):
            test_pixel[i] = (64, 64, 64)
        test_pixel.write()

    def reset(self):
        reset_pixel = neopixel.NeoPixel(self.pin, MAX_PIXELS)

        for i in range(MAX_PIXELS):
            reset_pixel[i] = (0, 0, 0)
        reset_pixel.write()
