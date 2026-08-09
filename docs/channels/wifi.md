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
| `wifi.ap_ssid` | `""` | Name of the device's own setup network (see below). Leave it empty to use `"<device.name>-setup"`. |
| `wifi.ap_password` | `""` | Password for the setup network. Leave it empty for an open (no password) network. |

Set them before first boot, or change them later — the device reconnects on
its own, no reboot needed (it can take a few seconds to notice the change).

## Can't connect? The device opens its own setup network

If no `wifi.ssid` is set, or the device can't join the one that is (wrong
password, network unreachable), it opens a temporary Wi-Fi network of its
own — `<device.name>-setup` by default — so you can still reach it.

Connect a phone or laptop to that network, then open the device's
[Web UI](webapi.md) in a browser at `http://192.168.4.1/` to fix your Wi-Fi
settings. Once you save working credentials, the device drops the setup
network immediately and joins your real network.

If a real Wi-Fi network is configured but temporarily unreachable, the device
tries a few times first before opening the setup network, and keeps it open
for about two minutes before trying your network again — so it doesn't sit
stuck on the setup network forever if the credentials are actually fine and
your router just restarted.

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
