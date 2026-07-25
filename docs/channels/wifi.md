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
  `start()` logs a warning, publishes `connected: false`, and idles forever
  (`asyncio.sleep_ms(IDLE_MS)` in a loop) without ever touching the radio
  again.
- **Radio is reset once at startup.** `_wlan.active(False)` then a
  `RADIO_RESET_MS` pause before the connect loop begins, to clear any stale
  state left over from a previous run.
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

`start()` runs for the lifetime of the device:

1. Read `wifi.ssid`/`wifi.password`. If `ssid` is empty, publish
   disconnected and idle forever — done.
2. Reset the radio (`active(False)`, sleep `RADIO_RESET_MS`).
3. Loop:
   - If already connected, publish connected + IP, sleep `MONITOR_MS`,
     and check again.
   - Otherwise publish disconnected, attempt `_connect()`. On success, loop
     back immediately. On failure, sleep the current backoff, then double
     it (capped at `BACKOFF_MAX_MS`).

### 1.2 Used configuration

Read from the `wifi` section of `config.json` (defaults in
`src/defaults.py`):

| Config key | Default | Used for |
|---|---|---|
| `wifi.ssid` | `""` | Network to join; empty disables the channel entirely |
| `wifi.password` | `""` | Network passphrase |

To configure it, set both fields in `config.json` (or `config.dev.json` for
local testing) before boot — there's no runtime way to change them from a
running device yet (no `wifi` key is exposed through the Web API allow-list
or the MQTT `state/update` allow-list), so a Wi-Fi network change currently
means editing the file and rebooting.

`runtime.wifi.connected`/`runtime.wifi.ip` are not configuration — they're
produced by this channel at runtime and only ever read by others.

## 2. Exposed functions

`WifiChannel` (`src/channels/wifi.py`) implements the standard
[`Channel`](index.md) interface plus the internals that do the work:

| Function | Type | What it does |
|---|---|---|
| `start()` | `Channel` interface | Runs the workflow in [1.1](#11-basic-workflow); the device's single long-lived entry point for this channel |
| `stop()` | `Channel` interface | Disconnects and deactivates the radio |
| `_connect(ssid, password)` | internal | One bounded connection attempt, `await`-polled up to `CONNECT_TIMEOUT_MS` |
| `_publish(connected, ip)` | internal | De-dupes against the last known state, logs on change, and writes `runtime.wifi.connected`/`ip` |
