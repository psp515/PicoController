---
layout: default
title: Wi-Fi
parent: Channels
nav_order: 1
---

# Wi-Fi

Wi-Fi isn't something you control the device *with* — it just keeps the device
connected to your network so the [MQTT channel](mqtt.md) can reach it.

## Setting it up

Put your network name and password in `config.json`:

| Setting | Default | What it does |
|---|---|---|
| `wifi.ssid` | `""` | Your Wi-Fi network name. Leave it empty to turn Wi-Fi off — which also turns MQTT off, since MQTT needs the network. |
| `wifi.password` | `""` | Your Wi-Fi password. |

Set them before first boot, or change them later — the device reconnects on
its own, no reboot needed (it can take a few seconds to notice the change).

## Good to know

- **Automatic reconnect.** If the connection drops, the device keeps retrying
  until it's back online.
- **Safe credential changes.** If you enter the wrong password, the device
  notices it can't connect and automatically falls back to the last password
  that worked — so a typo can't lock you out.
- **Wi-Fi settings can't be changed over MQTT**, only by editing the config, so
  a misbehaving automation can never knock the device off your network.

{: .note }
> The connect-and-reconnect logic is documented in
> [Channel internals](../contributing/channels.md#wi-fi-channel).
