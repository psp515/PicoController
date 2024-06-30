from controller.strip.modes.static import Static
from controller.strip.utils.color import Color

OFF_COLOR = Color(0, 0, 0, 0)


class Off(Static):

    async def _color(self):
        return OFF_COLOR

    async def run(self):
        self.logger.debug("Starting off mode.")
        await self.animate_to_color(OFF_COLOR)
        self.logger.debug("Off mode finished.")

