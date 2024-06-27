import asyncio

from controller.strip.modes.static import Static, default_color


class StaticWhite(Static):
    async def _color(self):
        state = await self.state_manager.state()
        return default_color(state.brightness)
