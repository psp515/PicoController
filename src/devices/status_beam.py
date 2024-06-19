from machine import Pin
from uasyncio import sleep_ms

DELAY = 500
LED_R_PIN = 0
LED_G_PIN = 1
LED_B_PIN = 2


class StatusBeam:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, red_pin: int = LED_R_PIN, green_pin: int = LED_G_PIN, blue_pin: int = LED_B_PIN):
        if not getattr(self, '_initialized', False):
            self.red = Pin(red_pin, Pin.OUT)
            self.green = Pin(green_pin, Pin.OUT)
            self.blue = Pin(blue_pin, Pin.OUT)
            self._initialized = True
            self._off()

    def _off(self):
        """Turns off all colors."""
        self.red.off()
        self.green.off()
        self.blue.off()

    async def _blink(self, red: int, green: int, blue: int):
        """
        Blink LED.

        :param red: Boolean indicating if the red LED should be on.
        :param green: Boolean indicating if the green LED should be on.
        :param blue: Boolean indicating if the blue LED should be on.
        """
        self.red.value(red)
        self.green.value(green)
        self.blue.value(blue)

        await sleep_ms(DELAY)

        self._off()

    async def success(self):
        """Blinks the LED color to green."""
        await self._blink(0, 1, 0)

    async def error(self):
        """Blinks the LED color to red."""
        await self._blink(1, 0, 0)

    async def waiting(self):
        """Blinks the LED color to yellow."""
        await self._blink(1, 1, 0)

    async def configuration(self):
        """Blinks the LED color to blue."""
        await self._blink(0, 0, 1)
