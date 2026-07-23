---
layout: default
title: MQTT channel
---

[← Back to Channels](index.md)

# MQTT channel

Implemented in `src/channels/mqtt.py`, via the async `mqtt_as` client. Only
active if `mqtt.server` is set in the config — otherwise the channel idles.

## Connecting

1. Waits for `runtime.wifi.connected` before doing anything.
2. If `mqtt.ssl` is `true`, syncs the clock over NTP first (`mqtt.ntp_host`,
   default `pool.ntp.org`) — required for TLS certificate validation — and
   retries until it succeeds.
3. Connects using `mqtt.server`/`port`/`user`/`password`, retrying with a
   fixed backoff on failure.
4. On every (re)connect: subscribes to `<base_topic>/state/update` and
   publishes `"online"` (retained) to `<base_topic>/state/online`.

A last-will message of `"offline"` (retained) on `<base_topic>/state/online`
is registered at connect time, so the broker publishes it automatically if
the device drops off without a clean disconnect.

`<base_topic>` defaults to `controller/led/1`, configured via `mqtt.base_topic`.

## Topics

| Direction | Topic | Payload |
|---|---|---|
| Subscribes | `<base_topic>/state/update` | JSON patch — only `mode.current` / `mode.brightness` / `mode.speed` / `mode.on` and `leds.count` are applied; any other key is silently dropped |
| Publishes, retained | `<base_topic>/state/full` | `{"mode": {...}, "leds": {"count": 144}}`, sent whenever the state changes |
| Publishes, retained (last will) | `<base_topic>/state/online` | `"online"` while connected, `"offline"` if the device drops off unexpectedly |

## Examples

Set brightness and switch mode:

```
mosquitto_pub -h <broker> -t <base_topic>/state/update \
  -m '{"mode": {"brightness": 80, "current": "rainbow"}}'
```

Watch the full state and online status:

```
mosquitto_sub -h <broker> -t '<base_topic>/state/#' -v
```

## Why the key allow-list?

Unlike the [Web API](webapi.md), which applies whatever patch it's given,
MQTT only accepts a fixed, small set of keys (`_filter_set_patch` in
`src/channels/mqtt.py`). MQTT topics are often wired into shared home
automation systems, so this keeps a stray or malformed automation from being
able to rewrite the device's Wi-Fi/MQTT credentials or other config — only
the fields you'd actually want a dashboard/voice assistant to touch.
