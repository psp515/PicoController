WIPE_INTERVAL_MS = 30
WIPE_EDGE = 6
WIPE_STEPS = 40


class Animation:
    interval_ms = 40
    segmenting_compatible = True

    def __init__(self, mode, params):
        self.mode = mode
        self.params = params

    def render(self, buffer, count, frame):
        pass

    def apply_brightness(self, buffer, count):
        brightness = self.mode.brightness
        if brightness >= 100:
            return
        scale = (brightness * 255) // 100 + 1
        for i in range(count * 3):
            buffer[i] = buffer[i] * scale >> 8

    def wipe_frames(self, count):
        step = max(1, count // WIPE_STEPS)
        return (count + WIPE_EDGE + step - 1) // step

    def apply_wipe(self, buffer, count, frame):
        step = max(1, count // WIPE_STEPS)
        front = frame * step
        if front >= count + WIPE_EDGE:
            return False
        start = front - WIPE_EDGE
        if start < 0:
            start = 0
        for i in range(start, count):
            base = i * 3
            if i >= front:
                buffer[base] = 0
                buffer[base + 1] = 0
                buffer[base + 2] = 0
            else:
                num = front - i
                buffer[base] = buffer[base] * num // WIPE_EDGE
                buffer[base + 1] = buffer[base + 1] * num // WIPE_EDGE
                buffer[base + 2] = buffer[base + 2] * num // WIPE_EDGE
        return True
