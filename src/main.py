import uasyncio
from machine import reset

from configuration.extensions import initialize_configuration
from controller.strip_controller import StripController
from devices.strip import Strip
from configuration_server.configuration_server import ConfigurationServer
from devices.management_button import ManagementButton
from devices.status_beam import StatusBeam
from utils.logger import Logger
from mode import Mode


async def main():
    logger = Logger()

    logger.info('Initializing configuration.')
    initialize_configuration()

    logger.info('Initializing devices.')
    button = ManagementButton()
    beam = StatusBeam()
    strip = Strip()

    logger.info('Initializing device mode.')
    pressed = await button.wait_for_press()

    mode_name = 'Configuration' if pressed else 'Controller'

    mode = Mode()

    if pressed:
        await beam.blink(2)
        mode = ConfigurationServer()
    else:
        await beam.blink(1)
        mode = StripController()

    logger.info(f'Starting: {mode_name}.')
    await mode.start()

if __name__ == '__main__':
    try:
        uasyncio.run(main())
    finally:
        uasyncio.new_event_loop()
        reset()
