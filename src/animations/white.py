from animations.static import Static


class White(Static):
    def __init__(self, mode, params):
        super().__init__(mode, params)
        self._r = 255
        self._g = 255
        self._b = 255
