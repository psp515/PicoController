---
layout: default
title: Channels
nav_order: 4
has_children: true
---

# Channels

A **channel** is one input path into the device: IR remote, button, MQTT, Web
API, plus a `WifiChannel` that just keeps the network connection alive for the
others. Every channel is a `uasyncio` task started concurrently at boot from
`main.py` — none of them block startup on each other, and none of them touch
the LED strip or renderer directly.

The whole point of the abstraction: a channel's only job is to turn "something
happened" into a patch on the shared state, via `self.state.update(patch)`.
`StateManager` validates/clamps the patch, persists it (debounced), and
notifies everyone else (including the renderer) that something changed. A new
input method never needs to know anything about animations or the LED buffer,
and the renderer never needs to know anything about IR codes or MQTT topics.

## The `Channel` interface

Defined in `src/channels/base.py`:

```python
class Channel:
    name = "channel"

    def __init__(self, state, logger):
        self.state = state
        self.logger = logger

    async def start(self):
        pass

    async def stop(self):
        pass
```

- `name` — short identifier, used in log lines.
- `start()` — the channel's main coroutine; runs for the lifetime of the
  device. Long-running channels loop internally with
  `await asyncio.sleep_ms(...)` between polls; don't return early unless the
  channel is intentionally idle (see `MqttChannel`/`WifiChannel` when
  unconfigured).
- `stop()` — cooperative shutdown; not currently called from `main.py` but
  implemented for symmetry and for tests.

## Built-in channels

- [`WifiChannel`](wifi.md) (`src/channels/wifi.py`) — connects to Wi-Fi with
  exponential backoff, publishes `runtime.wifi.connected`/`ip`.
- [`ButtonChannel`](button.md) (`src/channels/button.py`) — polls the cover
  button, debounces in software, cycles modes / toggles on-off.
- [`MqttChannel`](mqtt.md) (`src/channels/mqtt.py`) — async MQTT (via
  `mqtt_as`), publishes full state retained, applies incoming patches from an
  allow-listed set of keys — see [MQTT](mqtt.md) for topics/payloads.

`IrChannel` (`src/channels/ir.py`) and `WebApiChannel`
(`src/channels/webapi.py`) exist in the codebase but aren't implemented/
tested to the point of having their own doc page yet.

## Adding a new channel

No other file needs to change — the renderer and every other channel are
unaware of each other. Steps:

1. Create `src/channels/<name>.py` from the template below.
2. Register an instance of it in the `channels` list in `main.py`.
3. If it needs config, add defaults for it to `DEFAULTS` in `src/defaults.py`
   (and to `config.dev.json` for local testing).

### Template

```python
import asyncio

from channels.base import Channel

POLL_MS = 100  # how often start() loops; pick something sane for the input


class MyChannel(Channel):
    name = "mychannel"

    def __init__(self, state, logger):
        super().__init__(state, logger)
        self._running = False
        # read any pins/config needed, e.g.:
        # self._pin = Pin(state.get("mychannel", "pin", default=4), Pin.IN)

    async def start(self):
        self._running = True
        self.logger.info("mychannel", "started")
        while self._running:
            # read input, and when something happened:
            # self.state.update({"mode": {"brightness": new_value}})
            await asyncio.sleep_ms(POLL_MS)

    async def stop(self):
        self._running = False
        self.logger.info("mychannel", "stopped")
```

### Rules to follow

- **Never** touch the LED strip / `Renderer` / `neopixel` directly — only ever
  call `self.state.update(patch)`.
- **Never** use `time.sleep()` or any other busy-wait — always
  `await asyncio.sleep_ms(...)` between polls, so the single event loop stays
  responsive to every other channel.
- **Never** allocate/print/decode inside a hardware interrupt handler if your
  channel is interrupt-driven (see `IrChannel`/`ir_rx` for the pattern: ISR
  just records a timestamp/flag, a `uasyncio` task does the real work).
- Read config through `self.state.get(...)` with an explicit `default=`, don't
  assume keys exist — configs can be old/partial.
- Use `self.logger.debug/info/warning/error(...)` with positional
  `{0}`/`{1}` placeholders, never `print()` or f-strings in the log call.
- If the channel is conditionally disabled (no config, e.g. `MqttChannel` with
  no `server` set), still keep `start()` alive with an idle sleep loop instead
  of returning immediately, matching the other channels' shape.

### Wiring it in

```python
# main.py
from channels.mychannel import MyChannel
...
channels = [
    WifiChannel(state, logger),
    ButtonChannel(state, logger),
    MqttChannel(state, logger),
    WebApiChannel(state, logger),
    IrChannel(state, logger),
    MyChannel(state, logger),
]
```
