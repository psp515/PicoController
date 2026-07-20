import asyncio

from machine import Pin

from channels.base import Channel

POLL_MS = 20
STABLE_POLLS = 2


class ButtonChannel(Channel):
    name = "button"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._pin = Pin(state.get("button", "pin", default=3), Pin.IN, Pin.PULL_UP)

    def _next_mode(self):
        names = sorted(self.state["modes"].keys())
        current = self.state.mode.current
        if current in names:
            return names[(names.index(current) + 1) % len(names)]
        return names[0]

    async def start(self):
        self._running = True
        stable = self._pin.value()
        last_raw = stable
        count = 0
        while self._running:
            raw = self._pin.value()
            if raw != last_raw:
                count = 0
                last_raw = raw
            else:
                count += 1
            if count >= STABLE_POLLS and raw != stable:
                stable = raw
                if stable == 0:
                    next_mode = self._next_mode()
                    self.logger.debug("button", "pressed, mode -> {0}", next_mode)
                    self.state.update({"mode": {"current": next_mode}})
            await asyncio.sleep_ms(POLL_MS)

    async def stop(self):
        self._running = False
