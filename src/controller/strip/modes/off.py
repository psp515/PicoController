from controller.strip.modes.static import Static
from controller.strip.utils.color import Color

OFF_COLOR = Color(0, 0, 0, 0)


class Off(Static):
    def color_for_led(self, n: int) -> Color:
        return OFF_COLOR

    async def run(self):
        self.logger.debug("Starting off mode.")
        await self.animate_to_color()
        self.logger.debug("Off mode finished.")
