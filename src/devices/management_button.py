from machine import Pin
import asyncio
import time

from configuration.features.button_options import ButtonOptions
from utils.logger import Logger


class ManagementButton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ManagementButton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            logger = Logger()
            options = ButtonOptions()
            logger.info(f"Initializing management button with pin {options.button_pin}")
            self.pin = Pin(options.button_pin, Pin.IN, Pin.PULL_UP)
            self.initialized = True

    async def wait_for_press(self, max_duration: int = 2000):
        """
        Waits for the button to be pressed for at least the specified minimum duration,
        but not more than the maximum duration.

        :param max_duration: Maximum duration in milliseconds to wait for the press.
        :return: Boolean indicating if the button was pressed for at least min_duration within max_duration.
        """
        start_time = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start_time) < max_duration:

            if self.pressed():
                return True

            await asyncio.sleep(1)

        return False

    def pressed(self):
        """
        Checks if the button is currently pressed.

        :return: Boolean indicating if the button is pressed.
        """
        return not self.pin.value()

