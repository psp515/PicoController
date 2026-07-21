import asyncio

from machine import Pin
from ir_rx.nec import NEC_8

from channels.base import Channel

POLL_MS = 50


class IrChannel(Channel):
    name = "ir"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        self._receiver = None
        self._data = 0
        self._pending = False

    def _on_code(self, data, addr, ctrl):
        if data < 0:
            return
        self._data = data
        self._pending = True

    async def start(self):
        self._running = True
        pin_no = self.state.get("ir", "pin", default=2)
        pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)
        self._receiver = NEC_8(pin, self._on_code)
        self.logger.info("ir", "listening on pin {0}", pin_no)
        while self._running:
            if self._pending:
                self._pending = False
                codes = self.state.get("ir", "codes", default={})
                patch = codes.get(str(self._data))
                if isinstance(patch, dict):
                    self.logger.debug("ir", "code {0} -> {1}", self._data, patch)
                    self.state.update(patch)
                else:
                    self.logger.debug("ir", "unmapped code {0}", self._data)
            await asyncio.sleep_ms(POLL_MS)

    async def stop(self):
        self._running = False
        if self._receiver:
            self._receiver.close()
            self._receiver = None
        self.logger.info("ir", "stopped")
