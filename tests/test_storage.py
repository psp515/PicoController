from storage import merge


def test_merge_overwrites_scalars():
    base = {"mode": {"current": "off", "brightness": 255}}
    merge(base, {"mode": {"current": "rainbow"}})
    assert base == {"mode": {"current": "rainbow", "brightness": 255}}


def test_merge_adds_new_keys():
    base = {"leds": {"count": 144}}
    merge(base, {"leds": {"pin": 5}})
    assert base == {"leds": {"count": 144, "pin": 5}}
