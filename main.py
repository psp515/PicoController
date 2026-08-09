import sys
import gc

if "lib" not in sys.path:
    sys.path.append("lib")
if "src" not in sys.path:
    sys.path.append("src")

import asyncio

from machine import WDT, Pin

from channels.button import ButtonChannel
from channels.mqtt import MqttChannel
from channels.wifi import WifiChannel
from logger.console import ConsoleAppender
from logger.logger import Logger
from renderer import Renderer
from state import StateManager
from storage import Storage


WDT_TIMEOUT_MS = 8000
HEARTBEAT_MS = 500


async def heartbeat(state, logger):
    led = Pin("LED", Pin.OUT)
    wdt = None
    if state.get("watchdog", "enabled", default=False):
        wdt = WDT(timeout=WDT_TIMEOUT_MS)
        logger.info("main", "watchdog armed, timeout {0}ms", WDT_TIMEOUT_MS)
    while True:
        led.toggle()
        if wdt:
            wdt.feed()
        await asyncio.sleep_ms(HEARTBEAT_MS)
        logger.debug("heartbeat", "Device free memory: {0}", gc.mem_free())


async def main():
    storage = Storage()
    state = StateManager(storage.load())
    logger = Logger(state, [ConsoleAppender()])
    state.set_logger(logger)
    state.revalidate()
    logger.info("main", "starting device {0} version {1}", state.device_id, state.version)

    if not state.get("leds", "on_after_boot", default=True):
        state.data()["mode"]["on"] = False
    else:
        state.data()["mode"]["on"] = True

    channels = [
        WifiChannel(state, logger),
        ButtonChannel(state, logger),
        MqttChannel(state, logger),
    ]

    asyncio.create_task(storage.autosave(state, logger))
    asyncio.create_task(Renderer(state, logger).start())
    for channel in channels:
        logger.debug("main", "starting channel {0}", channel.name)
        asyncio.create_task(channel.start())

    await heartbeat(state, logger)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.new_event_loop()
