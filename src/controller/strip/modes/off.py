from controller.strip.modes.mode import Mode
from controller.strip.utils.color import Color

OFF_COLOR = Color(0, 0, 0, 0)


class Off(Mode):
    def color_for_led(self, n: int) -> Color:
        return OFF_COLOR

    async def run(self):
        self.logger.debug("Starting off mode.")
        self.state = await self.state_manager.state()
        await self.animate_to_color()
        self.logger.debug("Off mode finished.")

