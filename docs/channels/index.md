---
layout: default
title: Channels
nav_order: 3
has_children: true
---

# Controlling the device

A **channel** is a way to control the device. They all work at the same time
and stay in sync — a change made one way shows up everywhere else instantly.

- [Button](button.md) — the physical button on the enclosure cover.
- [MQTT](mqtt.md) — control it from a home-automation system, phone app, or a
  script anywhere on your network.

Wi-Fi isn't a control method on its own — the [Wi-Fi channel](wifi.md) just
keeps the device connected so MQTT can reach it.

Every change you make is saved automatically, so after a power cut the device
comes back exactly as you left it.

{: .note }
> Want to add a new way to control the device in code? See
> [Channel internals](../contributing/channels.md) in the Contributing section.
