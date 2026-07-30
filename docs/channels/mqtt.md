---
layout: default
title: MQTT channel
parent: Channels
nav_order: 3
---

# MQTT channel

Implemented in `src/channels/mqtt.py`. Only active if `mqtt.enabled` is true
(the default), `mqtt.server` is set, **and** Wi-Fi is enabled (non-empty
`wifi.ssid`) — a disabled Wi-Fi channel implies a disabled MQTT channel.
When any of those isn't met, `start()` waits without touching the network
(logging which condition failed) until the `mqtt`/`wifi` config changes, so
enabling the channel at runtime (e.g. via the Web API) needs no reboot.

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
- **`mqtt.enabled` true, `mqtt.server` non-empty, `wifi.ssid` non-empty.**
  Any of them missing is an explicit "disabled" state, not an error — the
  channel logs the reason and waits for a config change.
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

`start()` runs for the lifetime of the device. It subscribes to internal
state changes once (`self.state.subscribe(self._on_change)` — the app's own
`StateManager` pub/sub, not MQTT), then loops over *sessions* (`_session`),
one per set of `mqtt`/`wifi` config. Each session, in order:

1. If the channel is disabled (`mqtt.enabled` false, empty `mqtt.server`, or
   empty `wifi.ssid`), log the reason and wait until the `mqtt`/`wifi`
   section changes — done.
2. Wait for `runtime.wifi.connected`.
3. Read `mqtt.base_topic`.
4. If `mqtt.ssl` is true, sync the clock over NTP, retrying until it works.
5. Build the `mqtt_as` client from config (`_build_client`).
6. Attempt `client.connect()`, retrying every `RETRY_MS` on failure.
7. Launch three background tasks that run for the rest of the session:
   - `_handle_up` — on every (re)connect, subscribes to
     `<base_topic>/state/update` and publishes `"online"` (retained).
   - `_handle_messages` — drains incoming messages, applies allow-listed
     patches to the shared state.
   - `_publish_state` — whenever the shared state changes, publishes the
     full state (retained).
8. `_session` itself then just waits — all real work happens in the three
   tasks above.

### 1.2.1 Config changes at runtime

The whole `mqtt` section is **dynamic**: whenever a state patch touches
`mqtt` or `wifi` (the client also carries the Wi-Fi credentials), the
current session ends — the three tasks are cancelled, `"offline"` is
published (retained) on the old `<base_topic>/state/online` so dashboards
don't show a ghost device, the client is closed — and a fresh session
starts, re-reading every `mqtt.*` value. Changing the broker, credentials,
`base_topic`, SSL settings, or single-topic mode therefore takes effect
without a reboot; the swap happens within `RETRY_SLICE_MS`-sized wait
slices, typically well under a second after the patch. Note the `mqtt`
section can only be patched via the [Web API](webapi.md) — it is
deliberately not on this channel's own allow-list
([3.1.1](#311-allow-list-for-the-update-topic)).

### 1.3 Used configuration

Read from the `mqtt` section of `config.json` (defaults in `src/defaults.py`):

| Config key | Default | Used for | Applies |
|---|---|---|---|
| `mqtt.enabled` | `true` | Master switch for the channel; `false` disables it regardless of the other keys | live — session restart ([1.2.1](#121-config-changes-at-runtime)) |
| `mqtt.server` | `""` | Broker host; empty disables the channel entirely | live — session restart |
| `mqtt.port` | `1883` | Broker port | live — session restart |
| `mqtt.user` / `mqtt.password` | `""` / `""` | Broker credentials | live — session restart |
| `mqtt.base_topic` | `controller/led/1` | Prefix for every topic this channel uses | live — session restart |
| `mqtt.use_single_topic_for_state_update` | `false` | When `true`, joins `state/update` and `state/full` into one topic, `<base_topic>/state` — see [2.2](#22-single-topic-mode) | live — session restart |
| `mqtt.ssl` | `false` | Enables TLS; also gates the NTP sync step | live — session restart |
| `mqtt.ssl_params` | `{}` | Passed through to `mqtt_as`; `server_hostname` is filled in from `mqtt.server` if not already set | live — session restart |
| `mqtt.ntp_host` | `pool.ntp.org` | NTP server used only when `mqtt.ssl` is true | live — session restart |

`_build_client` maps these onto the `mqtt_as` client config, plus a few
values not stored in `config.json`: `client_id` (from `state.device_id`,
derived from `machine.unique_id()`), `wifi_pw`/`ssid` (from the `wifi`
section, so `mqtt_as` can manage the Wi-Fi connection itself), `queue_len: 4`,
and `will` (the last-will topic/payload described in
[3.3](#33-last-will--online-status)).

## 2. Exposed functions

`src/channels/mqtt.py` holds two classes: `MqttTopics`, a small value object
that derives the topic strings from `base_topic` + single-topic mode, and
`MqttChannel`, which implements the standard [`Channel`](index.md) interface.
The channel's methods are grouped into labelled sections (marker comments in
the source) that mirror the workflow.

**`MqttTopics`** — constructed from the current `base_topic` and the
single-topic flag; centralises the `/state` vs `/state/update` branching that
would otherwise be repeated per topic:

| Member | What it is |
|---|---|
| `base` | The configured `base_topic` prefix |
| `incoming_updates` | Topic subscribed to for incoming state patches (`<base>/state/update`, or `<base>/state` in single-topic mode) |
| `update_events` | Topic full-state events are published to (`<base>/state/full`, or `<base>/state` in single-topic mode) |
| `online_status` | The online/last-will topic (`<base>/state/online`) |

**`MqttChannel`** — `start`/`stop` at the top, everything else below in
sections:

| Function | Section | What it does |
|---|---|---|
| `start()` | Channel lifecycle | Loops over sessions per [1.2](#12-basic-workflow); the device's single long-lived entry point for this channel |
| `stop()` | Channel lifecycle | Ends the current session: cancels the background tasks, publishes `"offline"`, closes the client |
| `_session()` | Session state machine | Five-step story: wait-if-disabled, initialize, connect, start tasks, wait for restart — each step below polices itself and returns early if the session should end |
| `_wait_if_disabled()` | Session state machine | If `_disabled_reason()` is set, logs it and waits for a restart; returns `True` when it handled a disabled state |
| `_initialize_session()` | Session state machine | Waits for Wi-Fi, loads topic config, runs the NTP sync when TLS is on, builds the client; returns `False` if the session died mid-setup |
| `_connect_with_retries()` | Session state machine | `client.connect()` retry loop; returns `True` once connected, `False` if a restart interrupts it |
| `_start_session_tasks()` | Session state machine | Spawns the three background tasks |
| `_teardown()` | Session state machine | Cancels the session's tasks, publishes `"offline"` (retained), closes the client |
| `_on_change(patch)` | Restart & publish signalling | `StateManager` subscriber; a patch touching `mqtt`/`wifi` calls `_request_session_restart`, anything else `_request_state_publish` |
| `_request_session_restart()` / `_session_restart_requested()` / `_clear_session_restart_request()` / `_wait_for_session_restart()` | Restart & publish signalling | Intention-named wrappers around the session-restart event — firing, checking, clearing, and awaiting it |
| `_request_state_publish()` | Restart & publish signalling | Fires the event `_publish_state` waits on |
| `_session_alive()` | Restart & publish signalling | `True` while the channel runs and no session restart is pending; guards every wait/retry loop |
| `_sleep_unless_session_restarts(ms)` | Restart & publish signalling | Sliced sleep that returns early when a session restart is requested |
| `_disabled_reason()` | Enablement | Returns why the channel can't run (`mqtt.enabled` false, no server, Wi-Fi disabled) or `None` when it can |
| `_wait_for_wifi_connected()` | Connection setup | Polls `runtime.wifi.connected` until up (or a restart intervenes) |
| `_load_topic_config()` | Connection setup | Reads `base_topic`/single-topic mode into a fresh `MqttTopics` |
| `_sync_time_with_retries()` / `_sync_time()` | Connection setup | NTP clock sync (needed for TLS); the retry wrapper plus the one-shot sync |
| `_build_client()` | Connection setup | Builds the `mqtt_as` config dict and `MQTTClient` instance from `state` |
| `_handle_up()` | Background tasks | Re-subscribes and re-announces online status after every connect/reconnect |
| `_handle_messages()` | Background tasks | Parses incoming JSON, filters it through the allow-list, applies it to `state` |
| `_filter_set_patch(patch)` | Background tasks | Implements the allow-list in [3.1.1](#311-allow-list-for-the-update-topic) |
| `_publish_state()` | Background tasks | Publishes the retained full-state payload whenever `state` changes |

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
| Publishes, retained | `<base_topic>/state/full` | `{"device": "<id>", "mode": {...}, "leds": {"count": 144, "segmenting": {...}}}`, sent whenever the state changes |
| Publishes, retained (last will) | `<base_topic>/state/online` | `"online"` while connected, `"offline"` if the device drops off unexpectedly |

Every published state payload carries a `"device"` field with the device's
own id (`StateManager.device_id`, derived from `machine.unique_id()`), and
`_handle_messages` drops any incoming patch whose `device` equals that id.
In the default two-topic setup this never triggers; it exists for single-topic
mode below. External senders should simply omit the field.

### 2.2 Single-topic mode

Some integrations want commands and state on one topic. Set
`mqtt.use_single_topic_for_state_update: true` and both directions collapse
onto `<base_topic>/state`:

| Direction | Topic | Payload |
|---|---|---|
| Subscribes | `<base_topic>/state` | Same allow-listed JSON patch as `state/update` |
| Publishes, retained | `<base_topic>/state` | Same full-state payload as `state/full` |

Because the device is now subscribed to the topic it publishes on, the broker
echoes its own state publishes back (MQTT 3.1.1, which `mqtt_as` speaks, has
no MQTT 5 "No Local" subscription option). The `"device"` field is what breaks
that loop: the device ignores any payload stamped with its own id — including
the retained copy replayed on every reconnect. `<base_topic>/state/online`
is unaffected by this switch.

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

Reverse the animation direction, so it plays from the far end of the strip
(applies to every mode except `off` — see
[Direction](../animations/index.md#direction)):

```
mosquitto_pub -h <broker> -t <base_topic>/state/update \
  -m '{"mode": {"direction": "backward"}}'
```

Back to normal, and set the global color at the same time (any allow-listed
`mode` fields can share one patch):

```
mosquitto_pub -h <broker> -t <base_topic>/state/update \
  -m '{"mode": {"direction": "forward", "color": [255, 120, 30]}}'
```

Anything other than `"forward"`/`"backward"` is ignored by validation and
the current direction is kept.

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
{"device": "e6614c311b331b35", "mode": {"current": "rainbow", "brightness": 80, "speed": 10, "on": true, "color": [255, 120, 30], "direction": "forward"}, "leds": {"count": 144, "segmenting": {"enabled": true, "length": 5}}}
```

## 3.3 Last will / online status

`<base_topic>/state/online` is set as the connection's last-will topic at
connect time (`will=(...,"offline", True, 0)` in `_build_client`), so the
broker publishes `"offline"` (retained) automatically if the device
disconnects uncleanly — no code on the device runs to produce that message.
On a clean connect (and every reconnect), `_handle_up` explicitly publishes
`"online"` (retained) over the same topic. On a clean shutdown or a
config-triggered session restart ([1.2.1](#121-config-changes-at-runtime)),
the will doesn't fire, so `_teardown` publishes `"offline"` explicitly
before closing — important when `base_topic` changes, as nothing would ever
update the old topic again.

```
mosquitto_sub -h <broker> -t <base_topic>/state/online -v
```

Use this topic to drive an availability indicator in a dashboard or
automation system without polling — it only ever changes on an actual
connect/disconnect.
