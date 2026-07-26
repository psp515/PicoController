import asyncio

import machine
import neopixel

from animations.off import Off
from animations.registry import MODES

SEGMENT_LENGTH_MIN = 2


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

    def _resize(self, count):
        pin = self.state.get("leds", "pin", default=0)
        self.np = neopixel.NeoPixel(machine.Pin(pin), count)
        self.count = count
        self.logger.info("renderer", "leds count changed to {0}", count)

    def _make_animation(self):
        name = self.state.mode.current if self.state.mode.on else "off"
        if name not in MODES:
            self.logger.warning("renderer", "unknown mode {0}, falling back to off", name)
            name = "off"
        self.logger.debug("renderer", "mode -> {0}", name)
        params = self.state.mode.params(name)
        anim = MODES[name](self.state.mode, params)
        if isinstance(anim, Off):
            anim.fade_from(self.np.buf, self.count)
        return anim

    def _segment_count(self, anim):
        if not anim.segmenting_compatible:
            return self.count
        segmenting = self.state.get("leds", "segmenting", default={})
        if not segmenting.get("enabled"):
            return self.count
        length = segmenting.get("length", SEGMENT_LENGTH_MIN)
        if length < SEGMENT_LENGTH_MIN:
            length = SEGMENT_LENGTH_MIN
        if length >= self.count:
            return self.count
        return length

    def _tile(self, buf, seg_count):
        seg_size = seg_count * 3
        total = self.count * 3
        pos = seg_size
        while pos < total:
            chunk = min(seg_size, total - pos)
            buf[pos : pos + chunk] = buf[0:chunk]
            pos += chunk

    async def start(self):
        anim = None
        frame = 0
        while True:
            new_count = self.state.get("leds", "count", default=self.count)
            if new_count != self.count:
                self._resize(new_count)
                self._reload = True
            buf = self.np.buf
            if self._reload:
                self._reload = False
                anim = self._make_animation()
                frame = 0
            seg_count = self._segment_count(anim)
            anim.render(buf, seg_count, frame)
            if seg_count < self.count:
                self._tile(buf, seg_count)
            self.np.write()
            frame += 1
            await asyncio.sleep_ms(anim.interval_ms)
