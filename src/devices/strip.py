from machine import Pin
import neopixel
from configuration.features.strip_options import StripOptions

NEOPIXEL_PIN = 15
MAX_PIXELS = 300


class Strip:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, pin: int = NEOPIXEL_PIN):
        if not getattr(self, '_initialized', False):
            self.pin = Pin(pin, Pin.OUT)
            self._initialized = True

        self.length = StripOptions().length
        self.neopixel = neopixel.NeoPixel(self.pin, self.length)

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
