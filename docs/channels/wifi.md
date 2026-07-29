---
layout: default
title: Wifi channel
parent: Channels
nav_order: 1
---

# Wifi channel

Implemented in `src/channels/wifi.py`. It doesn't accept commands from
anything — it only keeps the station interface connected and publishes
`runtime.wifi.connected`/`runtime.wifi.ip`, which other channels can use.

## 1. Backoff-and-monitor loop

There's no external library here, just `network.WLAN(network.STA_IF)` driven
from a single `uasyncio` loop — connect, monitor while connected, and on drop
retry with exponential backoff.

### Constraints for it to work

- **`wifi.ssid` must be non-empty.** Empty is the explicit "disabled" state:
  `start()` logs a warning, publishes `connected: false`, and waits until the
  `wifi` config section changes — setting an `ssid` at runtime (e.g. via the
  Web API) enables the channel on the spot, no reboot.
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
  failure, the wait before retrying doubles each time up to
  `BACKOFF_MAX_MS`.
- **Downstream channels gate on state, not on this channel directly.**
  `WifiChannel` never calls into `MqttChannel`/`WebApiChannel` — it just
  writes `runtime.wifi.connected`/`ip` to shared state, and those channels
  poll that field themselves.

### 1.1 Basic workflow

`start()` runs for the lifetime of the device. It subscribes to state
changes once, then loops over *connection cycles* — one cycle per set of
credentials:

1. Read `wifi.ssid`/`wifi.password`. If `ssid` is empty, publish
   disconnected and wait until the `wifi` config section changes.
2. Reset the radio (`active(False)`, sleep `RADIO_RESET_MS`).
3. Loop (`_run()`), until the `wifi` config section changes:
   - If already connected, remember the credentials as last-known-good,
     publish connected + IP, sleep `MONITOR_MS`, and check again.
   - Otherwise publish disconnected, attempt `_connect()`. On success, loop
     back immediately. On failure, sleep the current backoff, then double
     it (capped at `BACKOFF_MAX_MS`).
4. When the config changes, disconnect and start the next cycle with the
   new credentials.

### 1.2 Changing credentials at runtime

The `wifi` section is **dynamic**: patch it through the [Web API](webapi.md)
(it is deliberately *not* on the MQTT allow-list) and the channel drops the
current connection and reconnects with the new credentials — no reboot.
Two things to know:

- **Reaction is not instant.** The running cycle notices the change at its
  next wake-up — worst case one backoff sleep (`BACKOFF_MAX_MS`, 30 s) or
  one in-flight connect attempt (`CONNECT_TIMEOUT_MS`, 15 s).
- **Bad credentials revert automatically.** If the new credentials fail
  `REVERT_ATTEMPTS` (3) connect attempts in a row without ever connecting,
  and a previous set of credentials had worked since boot, the channel
  writes those last-known-good credentials back into state (so the revert
  is also persisted) and reconnects with them, logging a warning. Without
  that safeguard a typo sent over Wi-Fi would strand the device until
  someone reached it physically. At boot with no last-known-good set the
  channel just keeps retrying, as before.

### 1.3 Used configuration

Read from the `wifi` section of `config.json` (defaults in
`src/defaults.py`):

| Config key | Default | Used for | Applies |
|---|---|---|---|
| `wifi.ssid` | `""` | Network to join; empty disables the channel entirely | live — channel reconnects (see [1.2](#12-changing-credentials-at-runtime)) |
| `wifi.password` | `""` | Network passphrase | live — channel reconnects (see [1.2](#12-changing-credentials-at-runtime)) |

Set both fields in `config.json` (or `config.dev.json` for local testing)
before first boot, or patch them later through the Web API — the channel
picks the change up at runtime. The MQTT `state/update` allow-list still
excludes `wifi` on purpose, so a stray automation can't rewrite the
credentials.

`runtime.wifi.connected`/`runtime.wifi.ip` are not configuration — they're
produced by this channel at runtime and only ever read by others.

## 2. Exposed functions

`WifiChannel` (`src/channels/wifi.py`) implements the standard
[`Channel`](index.md) interface plus the internals that do the work:

| Function | Type | What it does |
|---|---|---|
| `start()` | `Channel` interface | Runs the workflow in [1.1](#11-basic-workflow); the device's single long-lived entry point for this channel |
| `stop()` | `Channel` interface | Disconnects and deactivates the radio |
| `_run(ssid, password)` | internal | One connection cycle: connect/monitor/backoff loop for one set of credentials, exits when the `wifi` config changes; also implements the bad-credential revert in [1.2](#12-changing-credentials-at-runtime) |
| `_connect(ssid, password)` | internal | One bounded connection attempt, `await`-polled up to `CONNECT_TIMEOUT_MS` |
| `_on_change(patch)` | internal | `StateManager` subscriber; flags a reconnect when a patch touches the `wifi` section |
| `_publish(connected, ip)` | internal | De-dupes against the last known state, logs on change, and writes `runtime.wifi.connected`/`ip` |
