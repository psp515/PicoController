import uasyncio

from controller.strip.modes.static import Static, DEFAULT_COLOR


class StaticWhite(Static):
    def _color(self):
        color = DEFAULT_COLOR
        return self._include_brightness(color, self.state_manager.brightness)
