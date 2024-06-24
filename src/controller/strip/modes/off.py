from controller.strip.modes.static import Static


OFF_COLOR = (0, 0, 0)


class Off(Static):
    async def run(self):
        self.animate_to_color(OFF_COLOR)
