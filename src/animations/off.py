from animations.base import Animation

FADE_INTERVAL_MS = 30


class Off(Animation):
    interval_ms = 500

    def __init__(self, mode, params):
        super().__init__(mode, params)
        fade_ms = params.get("fade_ms", 600)
        self._fade_steps = max(1, fade_ms // FADE_INTERVAL_MS)
        self._fade_source = None

    def fade_from(self, buffer, count):
        self._fade_source = bytes(buffer[: count * 3])

    def render(self, buffer, count, frame):
        source = self._fade_source
        if source is None or frame >= self._fade_steps:
            for i in range(count * 3):
                buffer[i] = 0
            self.interval_ms = 500
            return
        remaining = self._fade_steps - frame
        num = remaining * remaining
        den = self._fade_steps * self._fade_steps
        for i in range(count * 3):
            buffer[i] = (source[i] * num) // den
        self.interval_ms = FADE_INTERVAL_MS
