def hex_to_rgb(value):
    if not isinstance(value, str):
        return None
    digits = value[1:] if value.startswith("#") else value
    if len(digits) != 6:
        return None
    try:
        return [int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16)]
    except ValueError:
        return None


def rgb_to_hex(rgb):
    return "#{0:02x}{1:02x}{2:02x}".format(
        max(0, min(255, int(rgb[0]))),
        max(0, min(255, int(rgb[1]))),
        max(0, min(255, int(rgb[2]))),
    )
