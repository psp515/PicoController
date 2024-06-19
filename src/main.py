import uasyncio

from server.web_server import WebServer
from controller.strip_controller import StripController
from devices.management_button import ManagementButton
from devices.status_beam import StatusBeam
from logging.logger import Logger
from mode import Mode

LED_R_PIN = 0
LED_G_PIN = 1
LED_B_PIN = 2

BUTTON_PIN = 14
NEOPIXEL_PIN = 15


async def main():
    logger = Logger()

    logger.info('Program Starting!')

    logger.info('Initializing devices.')
    button = ManagementButton()
    led_notifier = StatusBeam(LED_R_PIN, LED_G_PIN, LED_B_PIN)
    logger.info('Base devices initialized.')

    logger.info('Waiting for mode selection.')
    pressed = await button.wait_for_press(1000, 2000)

    mode_name = 'Configuration' if pressed else 'Controller'
    logger.info(f'Selected mode: {mode_name}')

    mode = Mode()

    if pressed:
        await led_notifier.configuration()
        # mode = WebServer()
    else:
        await led_notifier.success()
        # mode = StripController()

    logger.info('Starting mode.')
    await mode.start()

if __name__ == '__main__':
    uasyncio.run(main())
