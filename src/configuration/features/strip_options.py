from configuration.base_options import BaseOptions


class StripOptions(BaseOptions):
    NAME = "strip"

    def __init__(self):
        super().__init__()

    @property
    def length(self):
        return int(self.manager.read_config(self.NAME)["length"])

    @length.setter
    def length(self, value: int):
        self.manager.update_config(self.NAME, "length", str(value))