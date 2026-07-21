from state import StateManager


def test_get_returns_default_for_missing_path():
    state = StateManager({"mode": {"current": "static"}})
    assert state.get("mode", "brightness", default=42) == 42


def test_update_merges_patch_and_notifies_subscribers():
    state = StateManager({"mode": {"current": "static", "brightness": 128}})
    seen = []
    state.subscribe(lambda patch: seen.append(patch))

    state.update({"mode": {"brightness": 200}})

    assert state.get("mode", "brightness") == 200
    assert state.get("mode", "current") == "static"
    assert seen == [{"mode": {"brightness": 200}}]


def test_mode_helper_reads_through_state():
    state = StateManager({"mode": {"current": "rainbow", "brightness": 10, "speed": 3}})
    assert state.mode.current == "rainbow"
    assert state.mode.brightness == 10
    assert state.mode.speed == 3
