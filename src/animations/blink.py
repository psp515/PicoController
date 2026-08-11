from animations.base import Animation

BLINK_MIN_MS = 100
BLINK_MAX_MS = 600


class Blink(Animation):
    segmenting_compatible = False

    def __init__(self, mode, params):
        super().__init__(mode, params)
        color = mode.color
        self._r = color[0]
        self._g = color[1]
        self._b = color[2]
        speed = mode.speed
        if speed < 1:
            speed = 1
        half_period = BLINK_MAX_MS - speed * 5
        if half_period < BLINK_MIN_MS:
            half_period = BLINK_MIN_MS
        self.interval_ms = half_period

    def render(self, buffer, count, frame):
        lit = frame % 2 == 0
        r = self._r if lit else 0
        g = self._g if lit else 0
        b = self._b if lit else 0
        for i in range(0, count * 3, 3):
            buffer[i] = g
            buffer[i + 1] = r
            buffer[i + 2] = b
        if lit:
            self.apply_brightness(buffer, count)
