import time

# MicroPython-only helpers used by src/state.py. Patched onto the real `time`
# module so CPython can import and exercise that code under test.
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(time.monotonic() * 1000)
if not hasattr(time, "ticks_diff"):
    time.ticks_diff = lambda a, b: a - b
