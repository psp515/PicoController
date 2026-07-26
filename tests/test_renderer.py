import asyncio

from logger.logger import Logger
from renderer import Renderer, SEGMENT_LENGTH_MIN
from state import StateManager


def make_renderer(count=12, segmenting=None, mode_current="rainbow"):
    data = {
        "leds": {
            "count": count,
            "pin": 0,
            "segmenting": segmenting or {"enabled": False, "length": 2},
        },
        "mode": {"current": mode_current, "brightness": 100, "speed": 10, "on": True},
        "modes": {
            "rainbow": {},
            "static": {"color": [10, 20, 30]},
            "runner": {"color": [9, 8, 7], "length": 1},
        },
    }
    state = StateManager(data)
    logger = Logger(state)
    return Renderer(state, logger), state


def test_segment_count_full_strip_when_segmenting_disabled():
    renderer, _ = make_renderer(count=12, segmenting={"enabled": False, "length": 4})
    anim = renderer._make_animation()
    assert renderer._segment_count(anim) == 12


def test_segment_count_uses_configured_length_when_enabled():
    renderer, _ = make_renderer(count=12, segmenting={"enabled": True, "length": 4})
    anim = renderer._make_animation()
    assert renderer._segment_count(anim) == 4


def test_segment_count_clamps_below_minimum():
    renderer, _ = make_renderer(count=12, segmenting={"enabled": True, "length": 1})
    anim = renderer._make_animation()
    assert renderer._segment_count(anim) == SEGMENT_LENGTH_MIN


def test_segment_count_falls_back_to_full_strip_when_length_exceeds_count():
    renderer, _ = make_renderer(count=12, segmenting={"enabled": True, "length": 20})
    anim = renderer._make_animation()
    assert renderer._segment_count(anim) == 12


def test_segment_count_ignored_for_incompatible_mode():
    renderer, _ = make_renderer(
        count=12, segmenting={"enabled": True, "length": 4}, mode_current="static"
    )
    anim = renderer._make_animation()
    assert renderer._segment_count(anim) == 12


def test_segment_count_ignored_for_runner_mode():
    renderer, _ = make_renderer(
        count=12, segmenting={"enabled": True, "length": 4}, mode_current="runner"
    )
    anim = renderer._make_animation()
    assert renderer._segment_count(anim) == 12


def test_tile_repeats_segment_and_truncates_remainder():
    renderer, _ = make_renderer(count=7, segmenting={"enabled": True, "length": 2})
    buf = bytearray(21)
    buf[0:6] = bytes([1, 2, 3, 4, 5, 6])

    renderer._tile(buf, 2)

    assert bytes(buf) == bytes([1, 2, 3, 4, 5, 6] * 3 + [1, 2, 3])


def test_start_tiles_pixel_buffer_for_compatible_mode():
    renderer, _ = make_renderer(
        count=6, segmenting={"enabled": True, "length": 2}, mode_current="rainbow"
    )

    async def run_one_frame():
        task = asyncio.create_task(renderer.start())
        await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_one_frame())

    buf = renderer.np.buf
    segment = bytes(buf[0:6])
    assert bytes(buf[6:12]) == segment
    assert bytes(buf[12:18]) == segment
