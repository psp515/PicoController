---
layout: default
title: Channel internals
parent: Contributing
nav_order: 2
---

# Channel internals

How the control channels work under the hood, and how to add a new one. For
what each channel does from a user's point of view, see the
[Channels](../channels/index.md) section.

Every channel is a `uasyncio` task started concurrently at boot from `main.py`
— none of them block startup on each other, and none of them touch the LED
strip or renderer directly. A channel's only job is to turn "something
happened" into a patch on the shared state via `self.state.update(patch)`.
`StateManager` validates/clamps the patch, persists it (debounced), and
notifies everyone else (including the renderer). A new input method never needs
to know anything about animations or the LED buffer, and the renderer never
needs to know anything about button presses or MQTT topics.

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

## Wi-Fi channel

Implemented in `src/channels/wifi.py`. It doesn't accept commands from
anything — it only keeps the station interface connected and publishes
`runtime.wifi.connected`/`runtime.wifi.ip`, which other channels can use.

### Backoff-and-monitor loop

There's no external library here, just `network.WLAN(network.STA_IF)` driven
from a single `uasyncio` loop — connect, monitor while connected, and on drop
retry with exponential backoff.

- **`wifi.ssid` must be non-empty.** Empty is the explicit "disabled" state:
  `start()` logs a warning, publishes `connected: false`, and waits until the
  `wifi` config section changes — setting an `ssid` in the config enables the
  channel on the spot when the change lands, no reboot.
- **Radio is reset at the start of every connection cycle.**
  `_wlan.active(False)` then a `RADIO_RESET_MS` pause before the connect loop
  begins — once at startup and again after every config change, to clear any
  stale state left over from the previous cycle.
- **One connection attempt is a bounded wait, not a blocking call.**
  `_connect()` polls `_wlan.isconnected()` every 500 ms up to
  `CONNECT_TIMEOUT_MS`, `await`ing between polls — it never blocks the event
  loop.
- **Backoff only applies to failed attempts.** On success, the poll interval
  is the fixed `MONITOR_MS` and backoff resets to `BACKOFF_MIN_MS`; on
  failure, the wait before retrying doubles each time up to `BACKOFF_MAX_MS`.
- **Downstream channels gate on state, not on this channel directly.**
  `WifiChannel` never calls into `MqttChannel` — it just writes
  `runtime.wifi.connected`/`ip` to shared state, and those channels poll that
  field themselves.

`start()` subscribes to state changes once, then loops over *connection cycles*
— one cycle per set of credentials:

1. Read `wifi.ssid`/`wifi.password`. If `ssid` is empty, publish disconnected
   and wait until the `wifi` config section changes.
2. Reset the radio (`active(False)`, sleep `RADIO_RESET_MS`).
3. Loop (`_run()`), until the `wifi` config section changes:
   - If already connected, remember the credentials as last-known-good,
     publish connected + IP, sleep `MONITOR_MS`, and check again.
   - Otherwise publish disconnected, attempt `_connect()`. On success, loop
     back immediately. On failure, sleep the current backoff, then double it
     (capped at `BACKOFF_MAX_MS`).
4. When the config changes, disconnect and start the next cycle with the new
   credentials.

### Changing credentials at runtime

The `wifi` section is **dynamic**: apply a change to it (it is deliberately
*not* on the MQTT allow-list) and the channel drops the current connection and
reconnects with the new credentials — no reboot. Two things to know:

- **Reaction is not instant.** The running cycle notices the change at its next
  wake-up — worst case one backoff sleep (`BACKOFF_MAX_MS`, 30 s) or one
  in-flight connect attempt (`CONNECT_TIMEOUT_MS`, 15 s).
- **Bad credentials revert automatically.** If the new credentials fail
  `REVERT_ATTEMPTS` (3) connect attempts in a row without ever connecting, and
  a previous set of credentials had worked since boot, the channel writes those
  last-known-good credentials back into state (so the revert is also persisted)
  and reconnects with them, logging a warning. Without that safeguard a typo
  sent over Wi-Fi would strand the device until someone reached it physically.
  At boot with no last-known-good set the channel just keeps retrying.

### Wi-Fi exposed functions

| Function | Type | What it does |
|---|---|---|
| `start()` | `Channel` interface | Runs the connection-cycle loop; the device's single long-lived entry point for this channel |
| `stop()` | `Channel` interface | Disconnects and deactivates the radio |
| `_keep_connected(ssid, password)` | internal | One connection cycle: connect/monitor/backoff loop for one set of credentials, exits when a reconnect is requested |
| `_connect(ssid, password)` | internal | One bounded connection attempt, `await`-polled up to `CONNECT_TIMEOUT_MS` |
| `_reset_radio()` | internal | Deactivates the radio and pauses `RADIO_RESET_MS` before a cycle begins |
| `_on_change(patch)` | internal | `StateManager` subscriber; delegates to `_request_reconnect_if_wifi_changed` |
| `_request_reconnect_if_wifi_changed(patch)` / `_reconnect_requested()` / `_clear_reconnect_request()` / `_wait_for_wifi_config_change()` | internal | Intention-named wrappers around the channel's reconnect event |
| `_should_revert_credentials(...)` / `_revert_to_last_good(failures)` | internal | The bad-credential safeguard: decides when new credentials are hopeless and writes the last-known-good ones back into state |
| `_publish(connected, ip)` | internal | De-dupes against the last known state, logs on change, and writes `runtime.wifi.connected`/`ip` |

## Button channel

Implemented in `src/channels/button.py`. Polls a single push button on the
cover and turns short/long presses into state patches — no library, no
interrupts, just a debounced poll loop.

### Debounced poll loop

The pin is read every `POLL_MS`; a level only "counts" once it's been stable
for `STABLE_POLLS` consecutive polls, which filters out mechanical bounce
without any hardware debounce circuit. What happens next depends on how long
the button was held between the debounced press and the debounced release.

- **Active low, internal pull-up.** `Pin(pin_no, Pin.IN, Pin.PULL_UP)` — the
  pin reads `1` at rest and `0` while pressed, matching a button wired to
  ground.
- **Debounce is time-based, not edge-based.** A raw level change resets the
  stability counter (`count = 0`); only after `STABLE_POLLS` polls in a row
  agree on the new level does it become the accepted `stable` value.
- **Timing is measured on release, not on press.** `pressed_at` is recorded on
  the debounced falling edge; the action taken is decided on the debounced
  rising edge, from `held_ms = ticks_diff(now, pressed_at)`.
- **No ISR.** A button doesn't need microsecond edge capture, so a plain
  `asyncio.sleep_ms(POLL_MS)` poll loop is simple enough and matches the
  project's "as simple as possible" rule.

`start()` runs for the lifetime of the device, polling every `POLL_MS`:

1. Debounce the raw pin level against `STABLE_POLLS`.
2. On a debounced **press** (level goes to `0`): record `pressed_at`.
3. On a debounced **release** (level goes back to `1`), classify `held_ms`:
   - `>= ABORT_MS`: held far too long, treated as an aborted gesture — no state
     change, just a log line.
   - `>= LONG_PRESS_MS`: toggles `mode.on` (device on/off).
   - otherwise (**short press**): if the device is currently **off**, turn it
     **on** (the press is consumed by waking the device, it does not also
     advance the mode); if already **on**, advance to the next mode via
     `state.mode.next_mode()`.

The press-timing thresholds (`POLL_MS`, `STABLE_POLLS`, `LONG_PRESS_MS`,
`ABORT_MS`) are module constants in `src/channels/button.py`, not config —
change them there and re-flash if the physical button needs different timing.
The pin is bound once at startup, so moving the button (`button.pin`) needs a
reboot; the same applies to `leds.pin`.

When `button.enabled` is `false`, the loop just sleeps (`DISABLED_POLL_MS`,
1 s) instead of polling the pin, picking the flag change up within a second.

### Button exposed functions

| Function | Type | What it does |
|---|---|---|
| `start()` | `Channel` interface | Runs the debounce/classify loop; the device's single long-lived entry point for this channel |
| `stop()` | `Channel` interface | Stops the poll loop |

## MQTT channel

Implemented in `src/channels/mqtt.py`. Only active if `mqtt.enabled` is true
(the default), `mqtt.server` is set, **and** Wi-Fi is enabled (non-empty
`wifi.ssid`) — a disabled Wi-Fi channel implies a disabled MQTT channel. If
`mqtt.certificate.validate` is also on (see
[Certificate validation](#certificate-validation)), the configured CA
certificate must be readable too. When any of those isn't met, `start()` waits
without touching the network (logging which condition failed) until the
`mqtt`/`wifi` config changes.

### Non-blocking, via `mqtt_as`

The channel is built entirely on `mqtt_as.MQTTClient` (Peter Hinch,
[`micropython-mqtt`](https://github.com/peterhinch/micropython-mqtt)), vendored
at `lib/mqtt_as.py` (`VERSION = (0, 8, 5)` as of this writing). Every network
call — `connect()`, `subscribe()`, `publish()`, iterating `client.queue` — is
an `await`ed coroutine running on the shared `uasyncio` loop. Nothing in this
channel calls `time.sleep()` or any other blocking socket API, matching the
project rule of never using the blocking `umqtt.simple`/`umqtt.robust` clients.

- **Wi-Fi first.** `start()` blocks (via a non-blocking poll loop, not a real
  block) on `runtime.wifi.connected` before doing anything else — MQTT never
  attempts to connect on its own.
- **`mqtt.enabled` true, `mqtt.server` non-empty, `wifi.ssid` non-empty.** Any
  of them missing is an explicit "disabled" state, not an error — the channel
  logs the reason and waits for a config change.
- **`machine.unique_id()` must be available** — it's hex-encoded into
  `client_id` (`StateManager.device_id`) so multiple devices on the same broker
  don't collide.
- **NTP reachability if `mqtt.ssl: true`.** TLS needs a correct clock for
  certificate validation, so `_sync_time()` runs once against `mqtt.ntp_host`
  before the first connect attempt, retrying every `NTP_RETRY_MS` until it
  succeeds.
- **Reconnection is `mqtt_as`'s job, not ours.** The channel doesn't implement
  its own reconnect loop for an established session — it awaits `client.up`,
  which `mqtt_as` sets/clears internally, and just re-subscribes and
  re-announces (`_handle_up`) whenever that event fires.
- **Incoming messages are queued, not handled inline.** `mqtt_as` buffers
  incoming messages in `client.queue` (`queue_len: 4`); `_handle_messages`
  drains it with `async for`, so a burst of messages can't block publishing or
  the rest of the event loop.

### Basic workflow

`start()` runs for the lifetime of the device. It subscribes to internal state
changes once (`self.state.subscribe(self._on_change)` — the app's own
`StateManager` pub/sub, not MQTT), then loops over *sessions* (`_session`), one
per set of `mqtt`/`wifi` config. Each session, in order:

1. If the channel is disabled (`mqtt.enabled` false, empty `mqtt.server`, empty
   `wifi.ssid`, or an unusable certificate when validation is on), log the
   reason and wait until the `mqtt`/`wifi` section changes.
2. Wait for `runtime.wifi.connected`.
3. Read `mqtt.base_topic`.
4. If `mqtt.ssl` is true, sync the clock over NTP, retrying until it works.
5. Build the `mqtt_as` client from config (`_build_client`).
6. Attempt `client.connect()`, retrying every `RETRY_MS` on failure.
7. Launch three background tasks for the rest of the session:
   - `_handle_up` — on every (re)connect, subscribes to
     `<base_topic>/state/update` and publishes `"online"` (retained).
   - `_handle_messages` — drains incoming messages, applies allow-listed
     patches to the shared state.
   - `_publish_state` — whenever the shared state changes, publishes the full
     state (retained).
8. `_session` itself then just waits — all real work happens in the three tasks
   above.

The whole `mqtt` section is **dynamic**: whenever a state patch touches `mqtt`
or `wifi` (the client also carries the Wi-Fi credentials), the current session
ends — the three tasks are cancelled, `"offline"` is published (retained) on
the old `<base_topic>/state/online` so dashboards don't show a ghost device,
the client is closed — and a fresh session starts, re-reading every `mqtt.*`
value. The swap happens within `RETRY_SLICE_MS`-sized wait slices, typically
well under a second. The `mqtt` section is deliberately kept off this channel's
own allow-list (see [Allow-list](#allow-list-for-the-update-topic)), so an
incoming MQTT patch can't reconfigure the connection it arrives on.

### Installing a different `mqtt_as` version

`lib/mqtt_as.py` is a vendored copy, not a package dependency — there's no
`pip`/`mip` step on-device. To use a different version:

1. Download the replacement `mqtt_as.py` from the
   [`micropython-mqtt`](https://github.com/peterhinch/micropython-mqtt) repo
   and overwrite `lib/mqtt_as.py` wholesale — don't hand-edit the existing file
   into a mix of versions.
2. Keep the same public surface this project relies on:
   `from mqtt_as import MQTTClient, config as mqtt_config`, and the `config`
   dict keys read/written in `_build_client` (`client_id`, `server`, `port`,
   `user`, `password`, `ssid`, `wifi_pw`, `will`, `queue_len`, `ssl`,
   `ssl_params`). If a newer version renames or drops one of these,
   `_build_client` needs a matching update.
3. `tests/conftest.py` stubs `mqtt_as` for host-side testing — if you start
   depending on new fields/behavior, make sure that stub still satisfies
   `channels/mqtt.py`'s imports before `pytest` will pass.
4. Re-run the usual checks (`ruff check`, `compileall`, `pytest`; see the
   [Development guide](../development.md)), then copy `lib/` back onto the
   device as in [Manual setup](../setup.md).

### Certificate validation

`mqtt.ssl: true` alone gets you an encrypted connection but does **not** verify
the broker's identity — `mqtt_as`/`ussl` accept any certificate the server
presents, so a network-position attacker can MITM the TLS session undetected.
Setting `mqtt.certificate.validate: true` closes that gap: `_build_client`
reads the CA certificate from `certs/<mqtt.certificate.name>` on the device
filesystem (PEM or DER — the underlying `ssl.wrap_socket`/mbedtls binding
accepts either) and passes it as `cadata` with `cert_reqs = ssl.CERT_REQUIRED`,
so the handshake fails closed if the broker's chain doesn't validate against
it.

This is **fail-closed by design**: if `mqtt.ssl` and `mqtt.certificate.validate`
are both true but `mqtt.certificate.name` is empty, contains a path separator,
or the file isn't readable at `certs/<name>`, `_disabled_reason()` reports it
and the channel parks itself exactly like `mqtt.enabled: false` — it does
**not** silently fall back to unverified TLS. Fixing it (uploading the missing
cert, correcting the name) needs no reboot: any `mqtt.*` save re-triggers the
session restart, which re-runs the check.

Notes:

- `mqtt.server` must be a hostname, not a bare IP — certificate verification
  checks the presented cert against `ssl_params.server_hostname` (filled in
  from `mqtt.server`), and CA-issued certs aren't issued for IP addresses.
- To get a DER file from a PEM one:
  `openssl x509 -in cert.pem -outform der -out cert.der`.
- A handshake failure caused by a genuinely wrong/expired cert isn't treated
  specially — it surfaces as an `OSError` in `_connect_with_retries`, logged
  and retried like any other connect failure.
- The default (`certificate.validate: false`) preserves the previous unverified
  behavior, so existing setups aren't affected until you opt in.

### Topics and payloads

All topics are prefixed with `<base_topic>` (`mqtt.base_topic`, default
`controller/led/1`):

| Direction | Topic | Payload |
|---|---|---|
| Subscribes | `<base_topic>/state/update` | JSON patch — only the allow-listed keys are applied; everything else is silently dropped |
| Publishes, retained | `<base_topic>/state/full` | `{"device": "<id>", "mode": {...}, "leds": {...}}`, sent whenever the state changes |
| Publishes, retained (last will) | `<base_topic>/state/online` | `"online"` while connected, `"offline"` if the device drops off unexpectedly |

Every published state payload carries a `"device"` field with the device's own
id (`StateManager.device_id`, derived from `machine.unique_id()`), and
`_handle_messages` drops any incoming patch whose `device` equals that id. In
the default two-topic setup this never triggers; it exists for single-topic
mode.

`<base_topic>/state/online` is set as the connection's last-will topic at
connect time (`will=(...,"offline", True, 0)` in `_build_client`), so the broker
publishes `"offline"` (retained) automatically if the device disconnects
uncleanly. On a clean connect (and every reconnect), `_handle_up` explicitly
publishes `"online"`. On a clean shutdown or a config-triggered session
restart, the will doesn't fire, so `_teardown` publishes `"offline"` explicitly
before closing — important when `base_topic` changes, as nothing would ever
update the old topic again.

#### Single-topic mode

Set `mqtt.use_single_topic_for_state_update: true` and both `state/update` and
`state/full` collapse onto `<base_topic>/state`. Because the device is now
subscribed to the topic it publishes on, the broker echoes its own state
publishes back (MQTT 3.1.1, which `mqtt_as` speaks, has no MQTT 5 "No Local"
option). The `"device"` field breaks that loop: the device ignores any payload
stamped with its own id — including the retained copy replayed on every
reconnect. `<base_topic>/state/online` is unaffected by the switch.

### Allow-list for the `update` topic

The `update` topic only accepts a fixed, small set of keys, not whatever patch
it's given (`ALLOWED_SET_KEYS` / `_filter_set_patch` in `src/channels/mqtt.py`):

| Key | Allowed fields |
|---|---|
| `mode` | `current`, `brightness`, `speed`, `on`, `color`, `direction` |
| `leds` | `count`, `segmenting` |

Anything outside this shape — an unknown top-level key, a field not listed, or
a non-object value — is dropped rather than applied; if *nothing* in the patch
survives filtering, the whole message is ignored and a warning is logged. MQTT
topics are commonly wired into shared home-automation systems, so this keeps a
stray or malformed automation from rewriting the device's Wi-Fi/MQTT
credentials or any other config it shouldn't touch. `segmenting` is allowed as
a whole field; `length` is still floor-clamped to `2` by
`StateManager.update()` regardless of what's published (see
[Segmenting](../animations/index.md#segmenting)).

The color is a `hexColor` convenience that lives entirely in this channel, not
in `StateManager` (which only ever stores `mode.color` as an `[r, g, b]`
array). On the way in, `_resolve_hex_color` (in `_filter_set_patch`) turns a
`mode.hexColor` string into `mode.color` via `hex_to_rgb`
(`src/helpers/color.py`) before allow-list filtering — an invalid string is
logged and dropped. On the way out, `_publish_state` adds a `mode.hexColor`
string derived from `mode.color` with `rgb_to_hex`. `hexColor` is never
persisted and isn't itself on the allow-list.

### MQTT exposed functions

`src/channels/mqtt.py` holds two classes: `MqttTopics`, a small value object
that derives the topic strings from `base_topic` + single-topic mode, and
`MqttChannel`, which implements the standard `Channel` interface.

**`MqttTopics`:**

| Member | What it is |
|---|---|
| `base` | The configured `base_topic` prefix |
| `incoming_updates` | Topic subscribed to for incoming state patches (`<base>/state/update`, or `<base>/state` in single-topic mode) |
| `update_events` | Topic full-state events are published to (`<base>/state/full`, or `<base>/state` in single-topic mode) |
| `online_status` | The online/last-will topic (`<base>/state/online`) |

**`MqttChannel`:**

| Function | Section | What it does |
|---|---|---|
| `start()` | Channel lifecycle | Loops over sessions; the device's single long-lived entry point for this channel |
| `stop()` | Channel lifecycle | Ends the current session: cancels the background tasks, publishes `"offline"`, closes the client |
| `_session()` | Session state machine | Five-step story: wait-if-disabled, initialize, connect, start tasks, wait for restart |
| `_wait_if_disabled()` | Session state machine | If `_disabled_reason()` is set, logs it and waits for a restart |
| `_initialize_session()` | Session state machine | Waits for Wi-Fi, loads topic config, runs the NTP sync when TLS is on, builds the client |
| `_connect_with_retries()` | Session state machine | `client.connect()` retry loop; returns `True` once connected, `False` if a restart interrupts it |
| `_start_session_tasks()` | Session state machine | Spawns the three background tasks |
| `_teardown()` | Session state machine | Cancels the session's tasks, publishes `"offline"` (retained), closes the client |
| `_on_change(patch)` | Restart & publish signalling | `StateManager` subscriber; a patch touching `mqtt`/`wifi` calls `_request_session_restart`, anything else `_request_state_publish` |
| `_request_session_restart()` / `_session_restart_requested()` / `_clear_session_restart_request()` / `_wait_for_session_restart()` | Restart & publish signalling | Intention-named wrappers around the session-restart event |
| `_request_state_publish()` | Restart & publish signalling | Fires the event `_publish_state` waits on |
| `_session_alive()` | Restart & publish signalling | `True` while the channel runs and no session restart is pending |
| `_sleep_unless_session_restarts(ms)` | Restart & publish signalling | Sliced sleep that returns early when a session restart is requested |
| `_disabled_reason()` | Enablement | Returns why the channel can't run, or `None` when it can |
| `_certificate_disabled_reason()` | Enablement | Checks the certificate is usable when `mqtt.ssl` and `mqtt.certificate.validate` are both true |
| `_wait_for_wifi_connected()` | Connection setup | Polls `runtime.wifi.connected` until up |
| `_load_topic_config()` | Connection setup | Reads `base_topic`/single-topic mode into a fresh `MqttTopics` |
| `_sync_time_with_retries()` / `_sync_time()` | Connection setup | NTP clock sync (needed for TLS) |
| `_build_client()` | Connection setup | Builds the `mqtt_as` config dict and `MQTTClient` instance from `state` |
| `_handle_up()` | Background tasks | Re-subscribes and re-announces online status after every connect/reconnect |
| `_handle_messages()` | Background tasks | Parses incoming JSON, filters it through the allow-list, applies it to `state` |
| `_filter_set_patch(patch)` | Background tasks | Implements the allow-list above |
| `_resolve_hex_color(mode_fields)` | Background tasks | Converts an incoming `mode.hexColor` string into `mode.color` (`hex_to_rgb`) |
| `_publish_state()` | Background tasks | Publishes the retained full-state payload whenever `state` changes; adds `mode.hexColor` (`rgb_to_hex`) |

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
  channel is interrupt-driven — the ISR should just record a timestamp/flag and
  let a `uasyncio` task do the real work.
- Read config through `self.state.get(...)` with an explicit `default=`, don't
  assume keys exist — configs can be old/partial.
- Use `self.logger.debug/info/warning/error(...)` with positional
  `{0}`/`{1}` placeholders, never `print()` or f-strings in the log call.
- If the channel is conditionally disabled (no config), still keep `start()`
  alive with an idle sleep loop instead of returning immediately, matching the
  other channels' shape.

### Wiring it in

```python
# main.py
from channels.mychannel import MyChannel
...
channels = [
    WifiChannel(state, logger),
    ButtonChannel(state, logger),
    MqttChannel(state, logger),
    MyChannel(state, logger),
]
```
