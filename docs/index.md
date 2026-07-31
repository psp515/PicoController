---
layout: default
title: Home
nav_order: 1
---

# Pico Controller

PicoController turns a Raspberry Pi Pico W and a WS2812B ARGB LED strip into a
smart light you can control however suits you in the moment — the button on the
enclosure or a home automation system.

## What it can do

- **Turn the LEDs on or off**,
- **Switch between lighting modes:** (Static color, rainbow etc.)
- **Adjust brightness and speed**, shared across whichever mode is active.
- **Split the strip into repeating segments** — compatible modes (e.g.
  rainbow) repeat their pattern every N LEDs instead of stretching across the
  whole strip.
- **Remembers your settings.** Mode, brightness, speed, and on/off state all
  survive a power cycle — the strip comes back exactly as you left it.
- **Announces when it goes offline**, if you're watching it over MQTT (a
  retained "last will" message), so a dashboard or automation can notice.

## How you can control it

Pick whichever's convenient — they both work at the same time and stay in sync:

- **The button** on the enclosure cover — short press cycles modes, a longer
  press toggles the strip on/off.
- **MQTT** — for Home Assistant, Node-RED, [Senswave](https://senswave.net/) or any other automation system.

## Getting started

- [Manual setup](setup.md) — wiring, flashing MicroPython, copying the
  project on, and configuring it

## Using it

- [Channels](channels/index.md) — the ways to control it (button and MQTT)
- [Animations](animations/index.md) — the lighting modes and their controls

## Contributing / extending it

- [Contributing](contributing/index.md) — the developer docs: how it works
  internally, the architecture, setting up a dev environment, and how to add a
  new control method or lighting mode
