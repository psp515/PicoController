from animations.base import Animation

FRAME_MS = 30


class Runner(Animation):
    interval_ms = FRAME_MS
    segmenting_compatible = False

    def __init__(self, mode, params):
        super().__init__(mode, params)
        color = mode.color
        self._r = color[0]
        self._g = color[1]
        self._b = color[2]
        length = params.get("length", 5)
        if length < 1:
            length = 1
        self._length = length
        speed = mode.speed
        if speed < 1:
            speed = 1
        self._step = max(1, speed * 256 * FRAME_MS // 1000)
        self._span = length * 256
        self._half = self._span // 2
        self._zeros = None

    def render(self, buffer, count, frame):
        if self._zeros is None:
            self._zeros = bytes(count * 3)
        buffer[:] = self._zeros
        head_fp = frame * self._step
        head = head_fp >> 8
        frac = head_fp & 255
        for k in range(self._length + 1):
            pos = head - k
            if pos < 0:
                break
            dist = k * 256 + frac
            if dist >= self._span:
                break
            if dist <= self._half:
                scale = dist * 256 // self._half
            else:
                scale = (self._span - dist) * 256 // self._half
            i = (pos % count) * 3
            buffer[i] = self._g * scale >> 8
            buffer[i + 1] = self._r * scale >> 8
            buffer[i + 2] = self._b * scale >> 8
        self.apply_brightness(buffer, count)
