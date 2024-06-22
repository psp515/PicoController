import uasyncio

from configuration.extensions import initialize_configuration
from devices.strip import Strip
from configuration_server.configuration_server import ConfigurationServer
from devices.management_button import ManagementButton
from devices.status_beam import StatusBeam
from logging.logger import Logger
from mode import Mode


async def main():
    logger = Logger()

    logger.info('Initializing configuration.')
    initialize_configuration()

    logger.info('Initializing devices.')
    button = ManagementButton()
    strip = Strip()
    beam = StatusBeam()

    logger.info('Initializing device mode.')
    #pressed = await button.wait_for_press(1000, 2000)
    pressed = True

    mode_name = 'Configuration' if pressed else 'Controller'

    mode = Mode()

    if pressed:
        await beam.blink(2)
        mode = ConfigurationServer()
    else:
        await beam.blink(1)
        # mode = StripController()

    logger.info(f'Starting: {mode_name}.')
    await mode.start()

if __name__ == '__main__':
    try:
        uasyncio.run(main())
    finally:
        uasyncio.new_event_loop()
