from animations.base import Animation


class Runner(Animation):
    interval_ms = 50
    segmenting_compatible = False

    def __init__(self, mode, params):
        super().__init__(mode, params)
        color = mode.color
        length = params.get("length", 5)
        if length < 1:
            length = 1
        self._length = length
        self._trail = bytearray(length * 3)
        peak = length - 1
        for offset in range(length):
            dist = abs(2 * offset - peak)
            num = 2 * length - 2 * dist
            den = 2 * length
            base = offset * 3
            self._trail[base] = color[1] * num // den
            self._trail[base + 1] = color[0] * num // den
            self._trail[base + 2] = color[2] * num // den
        speed = mode.speed
        if speed < 1:
            speed = 1
        self.interval_ms = max(10, 1000 // speed)
        self._zeros = None

    def render(self, buffer, count, frame):
        if self._zeros is None:
            self._zeros = bytes(count * 3)
        buffer[:] = self._zeros
        trail = self._trail
        for offset in range(self._length):
            pos = frame - offset
            if pos < 0:
                continue
            i = (pos % count) * 3
            t = offset * 3
            buffer[i] = trail[t]
            buffer[i + 1] = trail[t + 1]
            buffer[i + 2] = trail[t + 2]
        self.apply_brightness(buffer, count)
