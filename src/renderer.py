import asyncio

import machine
import neopixel

from animations.registry import MODES


class Renderer:
    def __init__(self, state, logger):
        self.state = state
        self.logger = logger
        self.count = state["leds"]["count"]
        pin = state.get("leds", "pin", default=0)
        self.np = neopixel.NeoPixel(machine.Pin(pin), self.count)
        self._reload = True
        state.subscribe(self._on_change)
        self.logger.info("renderer", "leds count {0} pin {1}", self.count, pin)

    def _on_change(self, patch):
        self._reload = True

    def _make_animation(self):
        name = self.state.mode.current
        if name not in MODES:
            self.logger.warning("renderer", "unknown mode {0}, falling back to off", name)
            name = "off"
        self.logger.debug("renderer", "mode -> {0}", name)
        params = self.state.mode.params(name)
        return MODES[name](self.state.mode, params)

    async def start(self):
        anim = None
        frame = 0
        buf = self.np.buf
        size = self.count * 3
        while True:
            if self._reload:
                self._reload = False
                anim = self._make_animation()
                frame = 0
            anim.render(buf, self.count, frame)
            brightness = self.state.mode.brightness
            if brightness < 255:
                scale = brightness + 1
                for i in range(size):
                    buf[i] = buf[i] * scale >> 8
            self.np.write()
            frame += 1
            await asyncio.sleep_ms(anim.interval_ms)
