import asyncio

import channels.button as button_module
from channels.button import ButtonChannel
from logger.logger import Logger
from state import StateManager


class FakePin:
    def __init__(self):
        self.level = 1

    def value(self):
        return self.level


def make_channel(data):
    state = StateManager(data)
    logger = Logger(state)
    channel = ButtonChannel(state, logger)
    channel._pin = FakePin()
    return channel, state


def run_with_channel(channel, body):
    async def run():
        task = asyncio.create_task(channel.start())
        try:
            await body()
        finally:
            await channel.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    asyncio.run(run())


async def press(channel, hold=0.05):
    channel._pin.level = 0
    await asyncio.sleep(hold)
    channel._pin.level = 1
    await asyncio.sleep(0.05)


def test_short_press_turns_on(monkeypatch):
    monkeypatch.setattr(button_module, "POLL_MS", 1)
    channel, state = make_channel({"mode": {"on": False}, "modes": {"static": {}, "off": {}}})

    async def body():
        await asyncio.sleep(0.02)
        await press(channel)
        assert state.mode.on is True

    run_with_channel(channel, body)


def test_disabled_ignores_presses_until_reenabled(monkeypatch):
    monkeypatch.setattr(button_module, "POLL_MS", 1)
    monkeypatch.setattr(button_module, "DISABLED_POLL_MS", 1)
    channel, state = make_channel(
        {"button": {"enabled": False}, "mode": {"on": False}, "modes": {"static": {}, "off": {}}}
    )

    async def body():
        await asyncio.sleep(0.02)
        await press(channel)
        assert state.mode.on is False
        state.update({"button": {"enabled": True}})
        await asyncio.sleep(0.02)
        await press(channel)
        assert state.mode.on is True

    run_with_channel(channel, body)
