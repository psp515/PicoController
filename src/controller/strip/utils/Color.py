

class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, valid: bool = True):
        self._r = r
        self._g = g
        self._b = b
        self._valid = valid

    @property
    def is_valid(self) -> bool:
        return self._valid

    def rgb(self) -> tuple:
        return self._r, self._g, self._b

def _is_valid_rgb_hex(hex_color) -> bool:
    if isinstance(hex_color, str) and hex_color.startswith('#') and len(hex_color) == 7:
        try:
            int(hex_color[1:], 16)
            return True
        except ValueError:
            return False
    return False

def from_hex(value: object) -> Color:
    if  not isinstance(value, str):
        return Color()

    if not _is_valid_rgb_hex(value):
        return Color()

    hex_str = value.lstrip('#')
    _r, _g, _b = tuple(int(hex_str[i: i +2], 16) for i in (0, 2, 4))

    return Color(_r, _g, _b)

