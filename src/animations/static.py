from animations.base import Animation


class Static(Animation):
    interval_ms = 500

    def __init__(self, mode, params):
        super().__init__(mode, params)
        color = params.get("color", [255, 255, 255])
        self._r = color[0]
        self._g = color[1]
        self._b = color[2]

    def render(self, buffer, count, frame):
        r = self._r
        g = self._g
        b = self._b
        for i in range(0, count * 3, 3):
            buffer[i] = g
            buffer[i + 1] = r
            buffer[i + 2] = b
        self.apply_brightness(buffer, count)
