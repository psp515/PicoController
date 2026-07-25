from animations.off import Off
from state import StateManager


def make_off(fade_ms=90):
    state = StateManager({"mode": {"current": "off", "brightness": 50}, "modes": {"off": {"fade_ms": fade_ms}}})
    return Off(state.mode, state.mode.params("off"))


def test_render_without_fade_from_zeros_immediately():
    off = make_off()
    buffer = bytearray([1, 2, 3, 4, 5, 6])

    off.render(buffer, 2, 0)

    assert buffer == bytearray(6)


def test_fade_decays_monotonically_to_zero():
    off = make_off(fade_ms=90)
    source = bytearray([200, 100, 50])
    off.fade_from(source, 1)

    values = []
    buffer = bytearray(3)
    for frame in range(off._fade_steps + 1):
        off.render(buffer, 1, frame)
        values.append(bytes(buffer))

    for earlier, later in zip(values, values[1:]):
        assert later[0] <= earlier[0]
        assert later[1] <= earlier[1]
        assert later[2] <= earlier[2]
    assert values[-1] == bytes(3)


def test_fade_reaches_exactly_zero_at_fade_steps():
    off = make_off(fade_ms=60)
    off.fade_from(bytearray([255, 255, 255]), 1)
    buffer = bytearray(3)

    off.render(buffer, 1, off._fade_steps)

    assert buffer == bytearray(3)


def test_interval_ms_is_fast_during_fade_and_slow_once_off():
    off = make_off(fade_ms=90)
    off.fade_from(bytearray([255, 255, 255]), 1)
    buffer = bytearray(3)

    off.render(buffer, 1, 0)
    assert off.interval_ms < 500

    off.render(buffer, 1, off._fade_steps)
    assert off.interval_ms == 500


def test_snapshot_is_copied_not_referenced():
    off = make_off()
    source = bytearray([255, 255, 255])
    off.fade_from(source, 1)

    source[0] = 0

    buffer = bytearray(3)
    off.render(buffer, 1, 0)
    assert buffer[0] != 0
