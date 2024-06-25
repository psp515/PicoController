import uasyncio

from controller.strip.modes.static import Static
from controller.strip.utils.Color import Color


class StaticWhite(Static):
    async def _color(self):
        state = await self.state_manager.state()
        return Color(state.brightness, 255, 255, 255)
