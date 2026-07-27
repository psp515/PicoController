from animations.base import Animation


class Rainbow(Animation):
    interval_ms = 40

    def __init__(self, mode, params):
        super().__init__(mode, params)
        speed = mode.speed
        if speed < 1:
            speed = 1
        self._speed = speed
        self._wheel = bytearray(768)
        for pos in range(256):
            if pos < 85:
                r = 255 - pos * 3
                g = pos * 3
                b = 0
            elif pos < 170:
                p = pos - 85
                r = 0
                g = 255 - p * 3
                b = p * 3
            else:
                p = pos - 170
                r = p * 3
                g = 0
                b = 255 - p * 3
            base = pos * 3
            self._wheel[base] = g
            self._wheel[base + 1] = r
            self._wheel[base + 2] = b

    def render(self, buffer, count, frame):
        wheel = self._wheel
        scroll = frame - self.wipe_frames(count)
        if scroll < 0:
            scroll = 0
        offset = scroll * self._speed
        for i in range(count):
            src = (((i * 256) // count + offset) & 255) * 3
            dst = i * 3
            buffer[dst] = wheel[src]
            buffer[dst + 1] = wheel[src + 1]
            buffer[dst + 2] = wheel[src + 2]
        self.apply_brightness(buffer, count)
        self.apply_wipe(buffer, count, frame)
