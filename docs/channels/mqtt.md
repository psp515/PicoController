---
layout: default
title: MQTT channel
parent: Channels
nav_order: 3
---

# MQTT channel

Implemented in `src/channels/mqtt.py`. Only active if `mqtt.server` is set in
the config — otherwise `start()` idles forever (`asyncio.sleep_ms(IDLE_MS)` in
a loop) and never touches the network.

## What you can do with it

MQTT is the remote-control channel: anything that can talk to your MQTT
broker — a phone app, Home Assistant, Node-RED, a command line — can control
the device from anywhere on the network. Where the [button](button.md) gives
you two gestures, MQTT gives you the same controls and more:

- **Turn the lights on or off, switch the lighting mode, adjust brightness or
  speed, resize the strip, enable segmenting** — all by publishing a small
  JSON patch to one topic, taking effect immediately with no reboot; see
  [3.1](#31-message-examples-stateupdate) for the exact shape and copy-paste
  examples.
- **See the current state** — the device publishes its full state, retained,
  whenever anything changes, so a fresh subscriber gets it immediately; see
  [3.2](#32-message-examples-statefull).
- **Know if the device is alive** — an online/offline status updates
  automatically, even if the device loses power ungracefully; see
  [3.3](#33-last-will--online-status).

Settings that could break the device remotely (Wi-Fi credentials, pins,
broker address) are deliberately **not** controllable over MQTT — see the
[allow-list](#311-allow-list-for-the-update-topic). The rest of this page is
the technical detail: how the connection works and what exactly travels on
each topic.

## 1. Non-blocking, via `mqtt_as`

The channel is built entirely on `mqtt_as.MQTTClient` (Peter Hinch,
[`micropython-mqtt`](https://github.com/peterhinch/micropython-mqtt)), vendored
at `lib/mqtt_as.py` (`VERSION = (0, 8, 5)` as of this writing). Every network
call — `connect()`, `subscribe()`, `publish()`, iterating `client.queue` — is
an `await`ed coroutine running on the shared `uasyncio` loop. Nothing in this
channel calls `time.sleep()` or any other blocking socket API, matching the
project rule of never using the blocking `umqtt.simple`/`umqtt.robust` clients.

### Constraints for it to work

- **Wi-Fi first.** `start()` blocks (via a non-blocking poll loop, not a real
  block) on `runtime.wifi.connected` before doing anything else — MQTT never
  attempts to connect on its own.
- **`mqtt.server` must be non-empty.** Empty is the explicit "disabled" state,
  not an error.
- **`machine.unique_id()` must be available** — it's hex-encoded into
  `client_id` (`StateManager.device_id`) so multiple devices on the same
  broker don't collide.
- **NTP reachability if `mqtt.ssl: true`.** TLS needs a correct clock for
  certificate validation, so `_sync_time()` runs once against `mqtt.ntp_host`
  before the first connect attempt, retrying every `NTP_RETRY_MS` until it
  succeeds. If the network can't reach the NTP host, SSL mode never proceeds
  to connecting.
- **Reconnection is `mqtt_as`'s job, not ours.** The channel doesn't implement
  its own reconnect loop for an established session — it awaits
  `client.up`, which `mqtt_as` sets/clears internally, and just re-subscribes
  and re-announces (`_handle_up`) whenever that event fires.
- **Incoming messages are queued, not handled inline.** `mqtt_as` buffers
  incoming messages in `client.queue` (`queue_len: 4` in the client config);
  `_handle_messages` drains it with `async for`, so a burst of messages can't
  block publishing or the rest of the event loop.

### 1.1 Installing a different `mqtt_as` version

`lib/mqtt_as.py` is a vendored copy, not a package dependency — there's no
`pip`/`mip` step on-device. To use a different version:

1. Download the replacement `mqtt_as.py` from the
   [`micropython-mqtt`](https://github.com/peterhinch/micropython-mqtt)
   repo and overwrite `lib/mqtt_as.py` wholesale — don't hand-edit the
   existing file into a mix of versions.
2. Keep the same public surface this project relies on:
   `from mqtt_as import MQTTClient, config as mqtt_config` (see the top of
   `src/channels/mqtt.py`), and the `config` dict keys read/written in
   `_build_client` (`client_id`, `server`, `port`, `user`, `password`, `ssid`,
   `wifi_pw`, `will`, `queue_len`, `ssl`, `ssl_params`). If a newer version
   renames or drops one of these, `_build_client` needs a matching update.
3. `tests/conftest.py` stubs `mqtt_as` for host-side testing (it never runs
   for real on CPython) — if you start depending on new fields/behavior, make
   sure that stub still satisfies `channels/mqtt.py`'s imports before
   `pytest` will pass.
4. Re-run the usual checks (`ruff check`, `compileall`, `pytest`; see the
   [Development guide](../development.md)), then copy `lib/` back onto the
   device as in [Manual setup](../setup.md).

### 1.2 Basic workflow

`start()` runs once per boot, in order:

1. If `mqtt.server` is empty, idle forever — done.
2. Wait for `runtime.wifi.connected`.
3. Read `mqtt.base_topic`.
4. If `mqtt.ssl` is true, sync the clock over NTP, retrying until it works.
5. Build the `mqtt_as` client from config (`_build_client`).
6. Attempt `client.connect()`, retrying every `RETRY_MS` on failure.
7. Subscribe this channel to internal state changes
   (`self.state.subscribe(self._on_change)`) — this is the app's own
   `StateManager` pub/sub, not MQTT, and is what triggers republishing below.
8. Launch three background tasks that run for the rest of the device's
   lifetime:
   - `_handle_up` — on every (re)connect, subscribes to
     `<base_topic>/state/update` and publishes `"online"` (retained).
   - `_handle_messages` — drains incoming messages, applies allow-listed
     patches to the shared state.
   - `_publish_state` — whenever the shared state changes, publishes the
     full state (retained).
9. `start()` itself then just idle-loops — all real work happens in the three
   tasks above, so `stop()` can cancel them independently.

### 1.3 Used configuration

Read from the `mqtt` section of `config.json` (defaults in `src/defaults.py`):

| Config key | Default | Used for |
|---|---|---|
| `mqtt.server` | `""` | Broker host; empty disables the channel entirely |
| `mqtt.port` | `1883` | Broker port |
| `mqtt.user` / `mqtt.password` | `""` / `""` | Broker credentials |
| `mqtt.base_topic` | `controller/led/1` | Prefix for every topic this channel uses |
| `mqtt.ssl` | `false` | Enables TLS; also gates the NTP sync step |
| `mqtt.ssl_params` | `{}` | Passed through to `mqtt_as`; `server_hostname` is filled in from `mqtt.server` if not already set |
| `mqtt.ntp_host` | `pool.ntp.org` | NTP server used only when `mqtt.ssl` is true |

`_build_client` maps these onto the `mqtt_as` client config, plus a few
values not stored in `config.json`: `client_id` (from `state.device_id`,
derived from `machine.unique_id()`), `wifi_pw`/`ssid` (from the `wifi`
section, so `mqtt_as` can manage the Wi-Fi connection itself), `queue_len: 4`,
and `will` (the last-will topic/payload described in
[3.3](#33-last-will--online-status)).

## 2. Exposed functions

`MqttChannel` (`src/channels/mqtt.py`) implements the standard
[`Channel`](index.md) interface plus the coroutines that do the actual work:

| Function | Type | What it does |
|---|---|---|
| `start()` | `Channel` interface | Runs the workflow in [1.2](#12-basic-workflow); the device's single long-lived entry point for this channel |
| `stop()` | `Channel` interface | Cancels the background tasks and closes the client |
| `_build_client()` | internal | Builds the `mqtt_as` config dict and `MQTTClient` instance from `state` |
| `_sync_time()` | internal | One-shot NTP sync, only called when `mqtt.ssl` is true |
| `_handle_up()` | background task | Re-subscribes and re-announces online status after every connect/reconnect |
| `_handle_messages()` | background task | Parses incoming JSON, filters it through the allow-list, applies it to `state` |
| `_filter_set_patch(patch)` | internal | Implements the allow-list in [3.1.1](#311-allow-list-for-the-update-topic) |
| `_publish_state()` | background task | Publishes the retained full-state payload whenever `state` changes |

None of these are meant to be called from outside the channel — other code
only ever interacts with MQTT indirectly, by changing shared state (which
`_publish_state` picks up) or by publishing to `<base_topic>/state/update`
from off-device.

### 2.1 Topics

All topics are prefixed with `<base_topic>` (`mqtt.base_topic`, default
`controller/led/1`):

| Direction | Topic | Payload |
|---|---|---|
| Subscribes | `<base_topic>/state/update` | JSON patch — only the allow-listed keys are applied; everything else is silently dropped |
| Publishes, retained | `<base_topic>/state/full` | `{"mode": {...}, "leds": {"count": 144, "segmenting": {...}}}`, sent whenever the state changes |
| Publishes, retained (last will) | `<base_topic>/state/online` | `"online"` while connected, `"offline"` if the device drops off unexpectedly |

## 3.1 Message examples: `state/update`

Set brightness and switch mode:

```
mosquitto_pub -h <broker> -t <base_topic>/state/update \
  -m '{"mode": {"brightness": 80, "current": "rainbow"}}'
```

Resize the strip to 60 LEDs (the `Renderer` reallocates its buffer on the
fly, no reboot):

```
mosquitto_pub -h <broker> -t <base_topic>/state/update \
  -m '{"leds": {"count": 60}}'
```

Enable segmenting with a 5-LED repeat (only affects modes with
`segmenting_compatible = True`, e.g. `rainbow` — see
[Segmenting](../animations/index.md#segmenting)):

```
mosquitto_pub -h <broker> -t <base_topic>/state/update \
  -m '{"leds": {"segmenting": {"enabled": true, "length": 5}}}'
```

The device applies this the same way any other channel's patch is applied:
merged into `StateManager`, clamped/validated, persisted (debounced), and
picked up by the renderer immediately — no reboot or extra step needed.

### 3.1.1 Allow-list for the `update` topic

Unlike the [Web API](webapi.md), which applies whatever patch it's given,
this topic only accepts a fixed, small set of keys
(`ALLOWED_SET_KEYS` / `_filter_set_patch` in `src/channels/mqtt.py`):

| Key | Allowed fields |
|---|---|
| `mode` | `current`, `brightness`, `speed`, `on`, `color`, `direction` |
| `leds` | `count`, `segmenting` |

Anything outside this shape — an unknown top-level key, a field not listed
above, or a non-object value — is dropped rather than applied; if *nothing*
in the patch survives filtering, the whole message is ignored and a warning
is logged. MQTT topics are commonly wired into shared home-automation
systems, so this keeps a stray or malformed automation from rewriting the
device's Wi-Fi/MQTT credentials or any other config it shouldn't touch.

`segmenting` is allowed as a whole field, same as any `mode` field — the
filter only checks the field *name*, not its contents, so the full
`{"enabled": bool, "length": n}` object passes through in one patch (see
[Segmenting](../animations/index.md#segmenting) for what it does and which
modes respect it). `length` is still floor-clamped to `2` by
`StateManager.update()` regardless of what's published.

## 3.2 Message examples: `state/full`

Published retained, automatically, whenever the shared state changes —
nothing needs to be sent to trigger it. Subscribe to see the current state
on connect (thanks to the retained flag) and every change after:

```
mosquitto_sub -h <broker> -t <base_topic>/state/full -v
```

```json
{"mode": {"current": "rainbow", "brightness": 80, "speed": 10, "on": true, "color": [255, 120, 30], "direction": "forward"}, "leds": {"count": 144, "segmenting": {"enabled": true, "length": 5}}}
```

## 3.3 Last will / online status

`<base_topic>/state/online` is set as the connection's last-will topic at
connect time (`will=(...,"offline", True, 0)` in `_build_client`), so the
broker publishes `"offline"` (retained) automatically if the device
disconnects uncleanly — no code on the device runs to produce that message.
On a clean connect (and every reconnect), `_handle_up` explicitly publishes
`"online"` (retained) over the same topic.

```
mosquitto_sub -h <broker> -t <base_topic>/state/online -v
```

Use this topic to drive an availability indicator in a dashboard or
automation system without polling — it only ever changes on an actual
connect/disconnect.
