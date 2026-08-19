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


def patch_hold_timings(monkeypatch):
    monkeypatch.setattr(button_module, "POLL_MS", 1)
    monkeypatch.setattr(button_module, "OFF_FEEDBACK_MS", 40)
    monkeypatch.setattr(button_module, "CONFIG_REBOOT_DELAY_MS", 30)


def patch_reboot_recorder(monkeypatch):
    calls = []
    monkeypatch.setattr(
        button_module.application, "reboot_to_config", lambda state, logger: calls.append(True)
    )
    return calls


async def wait_until(predicate, timeout_s=1.0, interval_s=0.005):
    elapsed = 0.0
    while elapsed < timeout_s:
        if predicate():
            return True
        await asyncio.sleep(interval_s)
        elapsed += interval_s
    return predicate()


def test_long_hold_turns_off_then_reboots_while_still_held(monkeypatch):
    patch_hold_timings(monkeypatch)
    calls = patch_reboot_recorder(monkeypatch)
    channel, state = make_channel({"mode": {"on": True}, "modes": {"static": {}, "off": {}}})

    async def body():
        await asyncio.sleep(0.02)
        channel._pin.level = 0
        assert await wait_until(lambda: state.mode.on is False)
        assert calls == []
        assert await wait_until(lambda: calls == [True])
        await asyncio.sleep(0.05)
        assert calls == [True]

    run_with_channel(channel, body)


def test_long_hold_reboots_even_after_release(monkeypatch):
    patch_hold_timings(monkeypatch)
    calls = patch_reboot_recorder(monkeypatch)
    channel, state = make_channel({"mode": {"on": True}, "modes": {"static": {}, "off": {}}})

    async def body():
        await asyncio.sleep(0.02)
        channel._pin.level = 0
        assert await wait_until(lambda: state.mode.on is False)
        channel._pin.level = 1
        assert await wait_until(lambda: calls == [True])
        assert state.mode.on is False

    run_with_channel(channel, body)


def test_release_before_feedback_does_not_reboot(monkeypatch):
    patch_hold_timings(monkeypatch)
    # Generous threshold: a slow scheduler must not push a short press past it.
    monkeypatch.setattr(button_module, "OFF_FEEDBACK_MS", 500)
    calls = patch_reboot_recorder(monkeypatch)
    channel, state = make_channel({"mode": {"on": False}, "modes": {"static": {}, "off": {}}})

    async def body():
        await asyncio.sleep(0.02)
        await press(channel)
        await asyncio.sleep(0.1)
        assert calls == []
        assert state.mode.on is True

    run_with_channel(channel, body)


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
