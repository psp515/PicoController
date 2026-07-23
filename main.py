import sys

if "lib" not in sys.path:
    sys.path.append("lib")
if "src" not in sys.path:
    sys.path.append("src")

import asyncio

from machine import Pin

from channels.button import ButtonChannel
from channels.ir import IrChannel
from channels.mqtt import MqttChannel
from channels.webapi import WebApiChannel
from channels.wifi import WifiChannel
from logger.console import ConsoleAppender
from logger.logger import Logger
from renderer import Renderer
from state import StateManager
from storage import Storage


async def heartbeat():
    led = Pin("LED", Pin.OUT)
    while True:
        led.toggle()
        await asyncio.sleep_ms(500)


async def main():
    storage = Storage()
    state = StateManager(storage.load())
    logger = Logger(state, [ConsoleAppender()])
    state.set_logger(logger)
    logger.info("main", "starting device {0} version {1}", state.device_id, state.version)

    if not state.get("leds", "on_after_boot", default=True):
        state.data()["mode"]["on"] = False

    channels = [
        WifiChannel(state, logger),
        ButtonChannel(state, logger),
        MqttChannel(state, logger),
        WebApiChannel(state, logger),
        IrChannel(state, logger),
    ]

    asyncio.create_task(storage.autosave(state, logger))
    asyncio.create_task(Renderer(state, logger).start())
    for channel in channels:
        logger.debug("main", "starting channel {0}", channel.name)
        asyncio.create_task(channel.start())

    await heartbeat()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.new_event_loop()
