import uasyncio

from configuration.extensions import initialize_configuration
from devices.strip import Strip
from web_server.server import WebServer
from devices.management_button import ManagementButton
from devices.status_beam import StatusBeam
from logging.logger import Logger
from mode import Mode


async def main():
    logger = Logger()

    logger.info('Program Starting!')

    logger.info('Initializing Configuration.')
    initialize_configuration()

    logger.info('Initializing devices.')
    button = ManagementButton()
    strip = Strip()
    status_beam = StatusBeam()

    logger.info('Initializing device mode.')
    #pressed = await button.wait_for_press(1000, 2000)
    pressed = True

    mode_name = 'Configuration' if pressed else 'Controller'

    mode = Mode()

    if pressed:
        await status_beam.configuration()
        mode = WebServer()
    else:
        await status_beam.success()
        # mode = StripController()

    logger.info(f'Starting: {mode_name}.')
    await mode.start()

if __name__ == '__main__':
    uasyncio.run(main())
