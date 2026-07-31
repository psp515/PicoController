from helpers.color import hex_to_rgb, rgb_to_hex


def test_hex_to_rgb_parses_with_and_without_hash():
    assert hex_to_rgb("#ff781e") == [255, 120, 30]
    assert hex_to_rgb("ff781e") == [255, 120, 30]
    assert hex_to_rgb("00FF80") == [0, 255, 128]


def test_hex_to_rgb_rejects_malformed():
    assert hex_to_rgb("bad") is None
    assert hex_to_rgb("#12") is None
    assert hex_to_rgb("#1234567") is None
    assert hex_to_rgb("#zzzzzz") is None
    assert hex_to_rgb([255, 0, 0]) is None
    assert hex_to_rgb(None) is None


def test_rgb_to_hex_formats_and_clamps():
    assert rgb_to_hex([255, 120, 30]) == "#ff781e"
    assert rgb_to_hex([0, 0, 0]) == "#000000"
    assert rgb_to_hex([300, -5, 128]) == "#ff0080"
