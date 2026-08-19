import json

import application
from state import StateManager
from storage import Storage


def make_data(**overrides):
    data = {
        "system": {"default_mode": "normal", "boot_to_config": False},
        "mqtt": {"enabled": True, "server": "broker.local", "ssl": True},
    }
    for section, patch in overrides.items():
        data[section].update(patch)
    return data


class FakeStorage:
    def __init__(self):
        self.saved = []

    def save(self, data, logger=None):
        self.saved.append(json.loads(json.dumps(data)))


def resolve(**overrides):
    return application.resolve_boot_mode(StateManager(make_data(**overrides)))


def test_resolve_defaults_to_normal():
    assert resolve(system={"default_mode": "normal"}) == "normal"


def test_resolve_boot_flag_wins_over_default_mode():
    assert resolve(system={"default_mode": "mqtt-ssl", "boot_to_config": True}) == "config"


def test_resolve_mqtt_ssl_when_configured():
    assert resolve(system={"default_mode": "mqtt-ssl"}) == "mqtt-ssl"


def test_resolve_mqtt_ssl_falls_back_without_ssl():
    assert resolve(system={"default_mode": "mqtt-ssl"}, mqtt={"ssl": False}) == "normal"


def test_resolve_mqtt_ssl_falls_back_without_server():
    assert resolve(system={"default_mode": "mqtt-ssl"}, mqtt={"server": ""}) == "normal"


def test_resolve_mqtt_ssl_falls_back_when_mqtt_disabled():
    assert resolve(system={"default_mode": "mqtt-ssl"}, mqtt={"enabled": False}) == "normal"


def test_resolve_handles_missing_sections():
    assert application.resolve_boot_mode(StateManager({})) == "normal"


def test_clear_boot_flag_clears_and_saves():
    state = StateManager(make_data(system={"boot_to_config": True}))
    storage = FakeStorage()

    application.clear_boot_flag(state, None, storage)

    assert state.get("system", "boot_to_config") is False
    assert len(storage.saved) == 1
    assert storage.saved[0]["system"]["boot_to_config"] is False


def test_clear_boot_flag_skips_save_when_not_set():
    state = StateManager(make_data())
    storage = FakeStorage()

    application.clear_boot_flag(state, None, storage)

    assert storage.saved == []


def test_reboot_to_config_sets_flag_saves_then_resets(monkeypatch):
    state = StateManager(make_data())
    storage = FakeStorage()
    calls = []
    storage_save = storage.save

    def recording_save(data, logger=None):
        calls.append("save")
        storage_save(data, logger)

    storage.save = recording_save
    monkeypatch.setattr(application.machine, "reset", lambda: calls.append("reset"))

    application.reboot_to_config(state, None, storage)

    assert state.get("system", "boot_to_config") is True
    assert storage.saved[0]["system"]["boot_to_config"] is True
    assert calls == ["save", "reset"]


def test_reboot_to_config_uses_real_storage_by_default(tmp_path, monkeypatch):
    config_file = str(tmp_path / "config.json")
    monkeypatch.setattr(application, "Storage", lambda: Storage(config_file, config_file))
    monkeypatch.setattr(application.machine, "reset", lambda: None)
    state = StateManager(make_data())

    application.reboot_to_config(state, None)

    with open(config_file) as f:
        saved = json.load(f)
    assert saved["system"]["boot_to_config"] is True
