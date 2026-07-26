from state import StateManager


def test_get_returns_default_for_missing_path():
    state = StateManager({"mode": {"current": "static"}})
    assert state.get("mode", "brightness", default=42) == 42


def test_update_merges_patch_and_notifies_subscribers():
    state = StateManager({"mode": {"current": "static", "brightness": 40}})
    seen = []
    state.subscribe(lambda patch: seen.append(patch))

    state.update({"mode": {"brightness": 80}})

    assert state.get("mode", "brightness") == 80
    assert state.get("mode", "current") == "static"
    assert seen == [{"mode": {"brightness": 80}}]


def test_mode_helper_reads_through_state():
    state = StateManager({"mode": {"current": "rainbow", "brightness": 10, "speed": 3}})
    assert state.mode.current == "rainbow"
    assert state.mode.brightness == 10
    assert state.mode.speed == 3


def test_update_ignores_unknown_mode_current():
    state = StateManager({"mode": {"current": "static"}, "modes": {"static": {}, "rainbow": {}}})
    seen = []
    state.subscribe(lambda patch: seen.append(patch))

    state.update({"mode": {"current": "sparkle"}})

    assert state.mode.current == "static"
    assert seen == []


def test_update_applies_other_fields_when_mode_current_unknown():
    state = StateManager(
        {"mode": {"current": "static", "brightness": 40}, "modes": {"static": {}}}
    )

    state.update({"mode": {"current": "sparkle", "brightness": 80}})

    assert state.mode.current == "static"
    assert state.mode.brightness == 80


def test_update_allows_known_mode_current():
    state = StateManager({"mode": {"current": "static"}, "modes": {"static": {}, "rainbow": {}}})

    state.update({"mode": {"current": "rainbow"}})

    assert state.mode.current == "rainbow"


def test_update_clamps_brightness_and_speed_to_1_100():
    state = StateManager({"mode": {"current": "static", "brightness": 50, "speed": 50}})

    state.update({"mode": {"brightness": 500, "speed": -5}})

    assert state.mode.brightness == 100
    assert state.mode.speed == 1


def test_update_ignores_non_numeric_brightness():
    state = StateManager({"mode": {"current": "static", "brightness": 50}})
    seen = []
    state.subscribe(lambda patch: seen.append(patch))

    state.update({"mode": {"brightness": "bright"}})

    assert state.mode.brightness == 50
    assert seen == []


def test_update_ignores_bool_speed():
    state = StateManager({"mode": {"current": "static", "speed": 50}})

    state.update({"mode": {"speed": True}})

    assert state.mode.speed == 50


def test_mode_brightness_defaults_to_50():
    state = StateManager({"mode": {"current": "static"}})
    assert state.mode.brightness == 50


def test_update_clamps_segmenting_length_to_minimum():
    state = StateManager({"leds": {"count": 100, "segmenting": {"enabled": True, "length": 10}}})

    state.update({"leds": {"segmenting": {"length": 1}}})

    assert state.get("leds", "segmenting", "length") == 2


def test_update_ignores_non_numeric_segmenting_length():
    state = StateManager({"leds": {"count": 100, "segmenting": {"enabled": True, "length": 10}}})

    state.update({"leds": {"segmenting": {"length": "many"}}})

    assert state.get("leds", "segmenting", "length") == 10


def test_update_allows_valid_segmenting_length():
    state = StateManager({"leds": {"count": 100, "segmenting": {"enabled": False, "length": 2}}})

    state.update({"leds": {"segmenting": {"enabled": True, "length": 8}}})

    assert state.get("leds", "segmenting") == {"enabled": True, "length": 8}
