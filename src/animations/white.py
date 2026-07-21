from animations.base import Animation


class White(Animation):
    interval_ms = 500

    def render(self, buffer, count, frame):
        for i in range(count * 3):
            buffer[i] = 255
