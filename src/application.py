import asyncio
import gc

import machine
from machine import WDT, Pin

from logger.console import ConsoleAppender
from logger.logger import Logger
from renderer import Renderer
from state import StateManager
from storage import Storage

WDT_TIMEOUT_MS = 8000
HEARTBEAT_MS = 500

MODES = ("normal", "config", "mqtt-ssl")


def _mqtt_ssl_configured(state):
    return bool(
        state.get("mqtt", "enabled", default=True)
        and state.get("mqtt", "server", default="")
        and state.get("mqtt", "ssl", default=False)
    )


def resolve_boot_mode(state):
    if state.get("system", "boot_to_config", default=False):
        return "config"
    if state.get("system", "default_mode", default="normal") == "mqtt-ssl":
        if _mqtt_ssl_configured(state):
            return "mqtt-ssl"
    return "normal"


def clear_boot_flag(state, logger, storage=None):
    if not state.get("system", "boot_to_config", default=False):
        return
    state.data()["system"]["boot_to_config"] = False
    (storage or Storage()).save(state.data(), logger)
    if logger:
        logger.info("system", "boot_to_config flag cleared")


def reboot_to_config(state, logger, storage=None):
    state.data()["system"]["boot_to_config"] = True
    (storage or Storage()).save(state.data(), logger)
    if logger:
        logger.warning("system", "rebooting into config mode")
    machine.reset()


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

    mode = resolve_boot_mode(state)
    if mode == "config":
        clear_boot_flag(state, logger, storage)
    state.update({"runtime": {"system": {"mode": mode}}})
    logger.info("main", "boot mode {0}", mode)

    from channels.button import ButtonChannel
    from channels.network import NetworkChannel

    channels = [
        NetworkChannel(state, logger),
        ButtonChannel(state, logger),
    ]
    if mode != "config":
        from channels.mqtt import MqttChannel

        channels.append(MqttChannel(state, logger))
    if mode != "mqtt-ssl":
        from channels.webapi import WebApiChannel

        channels.append(WebApiChannel(state, logger))
    gc.collect()

    asyncio.create_task(storage.autosave(state, logger))
    asyncio.create_task(Renderer(state, logger).start())
    for channel in channels:
        logger.debug("main", "starting channel {0}", channel.name)
        asyncio.create_task(channel.start())

    await heartbeat(state, logger)
