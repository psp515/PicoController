import sys
import time
import types

# MicroPython-only helpers used by src/state.py. Patched onto the real `time`
# module so CPython can import and exercise that code under test.
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(time.monotonic() * 1000)
if not hasattr(time, "ticks_diff"):
    time.ticks_diff = lambda a, b: a - b

# channels/mqtt.py imports these MicroPython-only libraries at module level.
# Stub them so CPython can import and exercise that code under test.
if "mqtt_as" not in sys.modules:
    mqtt_as_stub = types.ModuleType("mqtt_as")
    mqtt_as_stub.config = {}

    class _MQTTClientStub:
        def __init__(self, cfg):
            self.cfg = cfg

    mqtt_as_stub.MQTTClient = _MQTTClientStub
    sys.modules["mqtt_as"] = mqtt_as_stub

if "machine" not in sys.modules:
    machine_stub = types.ModuleType("machine")

    class _RTCStub:
        def datetime(self, value=None):
            self.value = value

    machine_stub.RTC = _RTCStub
    machine_stub.unique_id = lambda: b"dev"
    sys.modules["machine"] = machine_stub
