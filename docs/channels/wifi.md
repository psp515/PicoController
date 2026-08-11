---
layout: default
title: Wi-Fi
parent: Channels
nav_order: 1
---

# Wi-Fi

Wi-Fi isn't something you control the device *with* — it just keeps the device
connected to your network so the [MQTT channel](mqtt.md) and the [Web
UI](webapi.md) can reach it.

## Setting it up

Put your network name and password in `config.json`, or use the Wi-Fi
section of the [Configuration page](webapi.md):

| Setting | Default | What it does |
|---|---|---|
| `wifi.ssid` | `""` | Your Wi-Fi network name. Leave it empty to turn Wi-Fi off — which also turns MQTT off, since MQTT needs the network. |
| `wifi.password` | `""` | Your Wi-Fi password. |
| `wifi.ap_ssid` | `"PicoController"` | Name of the device's own setup network (see below). |
| `wifi.ap_password` | `"Pico123456!"` | Password for the setup network. Leave it empty for an open (no password) network. |

{: .important }
> **Changes need a restart.** Unlike most settings, saving a new
> `wifi.ssid`/`wifi.password` (or `wifi.ap_ssid`/`wifi.ap_password`) doesn't
> take effect immediately — use the restart button on the [Web
> UI](webapi.md), or power-cycle the device, to actually try the new
> credentials. This is deliberate, not a bug: it keeps the Wi-Fi channel
> simple, and the setup network below is always there as a safe way back in
> if the new credentials turn out to be wrong.

## Can't connect? The device opens its own setup network

If no `wifi.ssid` is set, or the device can't join the one that is (wrong
password, network unreachable), it opens a temporary Wi-Fi network of its
own so you can still reach it. It tries a few times before giving up and
opening the setup network, and once open, **it stays open until you restart
the device** — it does not periodically retry your network on its own.

Connect a phone or laptop to that network, then open the device's
[Web UI](webapi.md) in a browser at `http://192.168.4.1/` to fix your Wi-Fi
settings, and restart the device to try them.

Not sure of your network's exact name? The Wi-Fi → Network section of the
[Configuration page](webapi.md) has a **Scan for networks** button; nearby
networks (with signal strength) then show up as suggestions on the Network
name field — handy while connected to the setup network.

## Good to know

- **Automatic reconnect.** If an established connection drops (router
  reboot, brief outage), the device keeps retrying with the *same*
  credentials until it's back online — no restart needed for that. A
  restart is only needed after you change the credentials themselves.
- **Wi-Fi settings can't be changed over MQTT**, only by editing the config
  or through the Web UI.

{: .note }
> The connect-and-reconnect logic is documented in
> [Channel internals](../contributing/channels.md#wi-fi-channel).
