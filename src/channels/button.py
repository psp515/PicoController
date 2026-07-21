import asyncio
import time

from machine import Pin

from channels.base import Channel

POLL_MS = 20
STABLE_POLLS = 2
LONG_PRESS_MS = 1500
ABORT_MS = 3000


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
        pin_no = self.state.get("button", "pin", default=3)
        self.logger.info("button", "listening on pin {0}", pin_no)
        stable = self._pin.value()
        last_raw = stable
        count = 0
        pressed_at = None
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
                    pressed_at = time.ticks_ms()
                    self.logger.debug("button", "down")
                else:
                    held_ms = time.ticks_diff(time.ticks_ms(), pressed_at) if pressed_at is not None else 0
                    self.logger.debug("button", "up after {0}ms", held_ms)
                    if held_ms >= ABORT_MS:
                        self.logger.debug("button", "held too long, aborted")
                    elif held_ms >= LONG_PRESS_MS:
                        self.logger.debug("button", "long press, mode -> off")
                        self.state.update({"mode": {"current": "off"}})
                    else:
                        next_mode = self._next_mode()
                        self.logger.debug("button", "short press, mode -> {0}", next_mode)
                        self.state.update({"mode": {"current": next_mode}})
                    pressed_at = None
            await asyncio.sleep_ms(POLL_MS)

    async def stop(self):
        self._running = False
        self.logger.info("button", "stopped")
