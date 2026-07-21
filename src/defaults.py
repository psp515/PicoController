DEFAULTS = {
    "device": {"name": "PicoController"},
    "leds": {
        "count": 144,
        "pin": 0,
        "on_after_boot": True,
    },
    "mode": {
        "current": "static",
        "brightness": 128,
        "speed": 10,
    },
    "modes": {
        "off": {},
        "white": {},
        "static": {"color": [255, 120, 30]},
        "rainbow": {},
        "runner": {"color": [0, 80, 255], "length": 5},
    },
    "wifi": {"ssid": "", "password": ""},
    "mqtt": {
        "server": "",
        "port": 1883,
        "user": "",
        "password": "",
        "base_topic": "picocontroller",
        "ssl": False,
        "ssl_params": {},
        "ntp_host": "pool.ntp.org",
    },
    "logging": {"enabled": False, "level": "info"},
    "button": {"pin": 3},
    "ir": {"pin": 2},
}
