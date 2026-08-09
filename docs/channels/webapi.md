---
layout: default
title: Web API
parent: Channels
nav_order: 4
---

# Web UI / Web API

A browser-based dashboard and configuration page, served by the device
itself — no app, no cloud account, nothing to install. It works over your
normal Wi-Fi network, and also over the device's own
[setup network](wifi.md#cant-connect-the-device-opens-its-own-setup-network)
if it can't join yours, so there's always a way in.

## Reaching it

Open the device's IP address (or `http://192.168.4.1/` if you're connected to
its setup network) in a browser:

- **`/`** — the dashboard: current mode, brightness, speed, color, on/off,
  which channels (MQTT, button, IR remote) are enabled, and a restart button.
- **`/modes`** — settings specific to each lighting mode (e.g. the runner's
  length, the off-fade duration).
- **`/config`** — device/network/system configuration, one page split into
  sections (device, Wi-Fi, LEDs, MQTT, logging, button, IR, Web API,
  watchdog). Changes take effect as soon as you hit Save — most settings
  apply immediately, a few need a restart (see the **Applies** column in the
  [Development guide](../development.md#top-level-keys)) — **Wi-Fi network
  settings always need a restart**, see [Wi-Fi](wifi.md).

Two sections have their own action button beyond Save:

- **LEDs → Test** lights the strip using whatever count is currently typed
  in the form, so you can confirm it before saving.
- **Wi-Fi → Scan for networks** lists nearby networks with signal strength —
  useful for getting the exact name right, especially while connected to the
  device's own setup network.

Both pages are just a thin layer over the same JSON API every other
integration uses (`GET`/`POST /json/state`) — nothing you can do here that
you couldn't do with a raw HTTP request, it's just easier.

## Settings

Configured in the `webapi` section of `config.json`:

| Setting | Default | What it does |
|---|---|---|
| `webapi.enabled` | `true` | Set to `false` to turn the dashboard/API off entirely. |

{: .note }
> There's no `webapi.enabled` toggle on the dashboard itself — turning it off
> from the page serving the toggle would lock you out of it. Use `/config`'s
> raw config editing, or edit `config.json` directly, if you need to disable
> it.

{: .note }
> How the server, routing, and static-file serving work internally is
> covered in
> [Channel internals](../contributing/channels.md#web-api--web-ui-channel).
