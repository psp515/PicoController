

class Color:
    def __init__(self, brightness: float, r: int = 0, g: int = 0, b: int = 0):

        if not 0 <= r <= 255 or not 0 <= g <= 255 or not 0 <= b <= 255:
            raise ValueError(f"Invalid RGB values. R={r}, G={g}, B={b}")

        if brightness < 0 or brightness > 1:
            raise ValueError(f"Invalid brightness value. Brightness={brightness}")

        self._r = r
        self._g = g
        self._b = b
        self._brightness = brightness

    def __getitem__(self, index: int) -> int:
        return self.rgb()[index]

    def __str__(self) -> str:
        return f"Color(brightness={self._brightness}, r={self._r}, g={self._g}, b={self._b}, adjusted_rgb={self.rgb()})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Color):
            return False
        return (self._brightness == other._brightness and
                self._r == other._r and
                self._g == other._g and
                self._b == other._b)

    def rgb(self) -> tuple:
        r = int(self._r * self._brightness)
        g = int(self._g * self._brightness)
        b = int(self._b * self._brightness)
        return r, g, b

def _is_valid_rgb_hex(hex_color) -> bool:
    if isinstance(hex_color, str) and hex_color.startswith('#') and len(hex_color) == 7:
        try:
            int(hex_color[1:], 16)
            return True
        except ValueError:
            return False
    return False

def from_hex(value: object, brightness: float) -> Color:
    if not isinstance(value, str):
        raise ValueError("Provided value color is not string.")

    if not _is_valid_rgb_hex(value):
        raise ValueError("Invalid hex color value.")

    hex_str = value.lstrip('#')
    _r, _g, _b = tuple(int(hex_str[i: i +2], 16) for i in (0, 2, 4))

    return Color(brightness=brightness, r=_r, g=_g, b=_b)
