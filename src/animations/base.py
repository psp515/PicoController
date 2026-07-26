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
