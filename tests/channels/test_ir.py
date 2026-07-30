import asyncio

import channels.ir as ir_module
from channels.ir import IrChannel
from logger.logger import Logger
from state import StateManager


def make_channel(data):
    state = StateManager(data)
    logger = Logger(state)
    return IrChannel(state, logger), state


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


def test_mapped_code_applies_patch(monkeypatch):
    monkeypatch.setattr(ir_module, "POLL_MS", 1)
    channel, state = make_channel(
        {"ir": {"codes": {"7": {"mode": {"on": False}}}}, "mode": {"on": True}}
    )

    async def body():
        await asyncio.sleep(0.02)
        assert channel._receiver is not None
        channel._on_code(7, 0, 0)
        await asyncio.sleep(0.02)
        assert state.mode.on is False

    run_with_channel(channel, body)


def test_disabled_has_no_receiver_until_reenabled(monkeypatch):
    monkeypatch.setattr(ir_module, "POLL_MS", 1)
    monkeypatch.setattr(ir_module, "DISABLED_POLL_MS", 1)
    channel, state = make_channel(
        {"ir": {"enabled": False, "codes": {"7": {"mode": {"on": False}}}}, "mode": {"on": True}}
    )

    async def body():
        await asyncio.sleep(0.02)
        assert channel._receiver is None
        state.update({"ir": {"enabled": True}})
        await asyncio.sleep(0.02)
        assert channel._receiver is not None
        channel._on_code(7, 0, 0)
        await asyncio.sleep(0.02)
        assert state.mode.on is False

    run_with_channel(channel, body)
