from animations.base import Animation


class Runner(Animation):
    interval_ms = 50
    segmenting_compatible = False

    def __init__(self, mode, params):
        super().__init__(mode, params)
        color = params.get("color", [255, 255, 255])
        self._r = color[0]
        self._g = color[1]
        self._b = color[2]
        length = params.get("length", 3)
        if length < 1:
            length = 1
        self._length = length
        speed = mode.speed
        if speed < 1:
            speed = 1
        self.interval_ms = max(10, 1000 // speed)
        self._zeros = None

    def render(self, buffer, count, frame):
        if self._zeros is None:
            self._zeros = bytes(count * 3)
        buffer[:] = self._zeros
        head = frame % count
        for offset in range(self._length):
            i = ((head - offset) % count) * 3
            buffer[i] = self._g
            buffer[i + 1] = self._r
            buffer[i + 2] = self._b
        self.apply_brightness(buffer, count)
