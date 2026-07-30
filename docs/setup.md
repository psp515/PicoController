---
layout: default
title: Manual setup
nav_order: 2
---

# Manual setup

There is no installer or build step — this is plain MicroPython. Setup is:
wire the hardware, flash the firmware once, then copy the project's files
onto the board.

## 1. Flash MicroPython

Download the official MicroPython firmware for the **Raspberry Pi Pico W**
(`.uf2` file) from micropython.org and flash it the usual way: hold the
**BOOTSEL** button while plugging the Pico W into USB, it will mount as a mass
storage drive, then drag the `.uf2` file onto it. The board reboots running
MicroPython.

## 2. Wire the hardware

### Pinout (defaults, configurable in `config.json`)

| Function             | Pico W pin | Config key    | Notes                                   |
|-----------------------|-----------|---------------|------------------------------------------|
| WS2812B data          | `GP0`     | `leds.pin`    | Required                                  |
| IR receiver (NEC)     | `GP2`     | `ir.pin`      | Optional, interrupt-driven                |
| Push button (cover)   | `GP3`     | `button.pin`  | Optional, active-low, internal pull-up    |

### WS2812B LED strip

- The strip is **5V logic and 5V power** (`WS2812B`, not the 12V `WS2811`
  variant — see the [future directions in CLAUDE.md](../.claude/CLAUDE.md) if
  you're bringing up 12V support instead).
- The Pico W's GPIO runs at **3.3V**. WS2812B data lines are commonly driven
  directly from a 3.3V GPIO and work reliably for short runs, but it's outside
  the chip's guaranteed spec — for longer strips or if you see flicker/glitches
  at the far end, add a level shifter (e.g. 74AHCT125) between `GP0` and the
  strip's data-in.
- Connect the strip's **ground to the Pico W's ground** even if the strip has
  its own 5V supply — a floating/missing common ground is the most common
  cause of erratic pixels.
- **Power budget**: each WS2812B LED can draw up to ~60mA at full white. At
  the default `leds.count: 144` that's up to ~8.6A — do **not** power the
  strip from the Pico's USB or 3V3 pin. Use a dedicated 5V supply sized for
  your LED count, wired directly to the strip's 5V/GND, sharing ground with
  the Pico.
- Add a large capacitor (e.g. 1000µF) across the strip's 5V/GND near the first
  pixel, and a ~300-500Ω resistor in series on the data line, per the usual
  WS2812B best practices — both reduce power-on glitches and ringing on the
  data line.

### IR receiver (optional)

- Any standard 3-pin NEC-compatible IR receiver module (e.g. TSOP38238/VS1838B
  style: `OUT` / `VCC` / `GND`) works.
- `OUT` → `GP2`, `VCC` → 3V3, `GND` → ground.
- The pin is read via a hardware interrupt: the ISR only records edge
  timestamps, decoding happens later in a `uasyncio` task — see the IR receiver
  note in [CLAUDE.md](../.claude/CLAUDE.md) if you're touching that code.

### Push button (optional)

- A simple momentary push button wired between `GP3` and ground.
- Configured `Pin.PULL_UP` in software (`ButtonChannel`), so no external
  pull-up resistor is needed — the pin reads high when open, low when pressed.
- Debounced entirely in software by polling every 20ms and requiring two
  stable consecutive reads before registering an edge.
- Press semantics (see the [Button channel](channels/button.md)): a short
  press turns the device on when it's off, or cycles to the next mode when
  it's on; a ~1s hold toggles on/off; holding past ~2s aborts the action.

## 3. Copy the project onto the device

Copy these onto the device's filesystem, preserving the folder layout:

- `main.py`
- `src/` (the application code)
- `lib/` (`mqtt_as.py`, `micropython_ir`, `microdot`)

Use whichever tool you're comfortable with — `mpremote`, `rshell`, or Thonny's
file browser all work:

```
mpremote cp -r src :src
mpremote cp -r lib :lib
mpremote cp main.py :main.py
```

Do **not** copy `tests/`, `helpers/`, or `docs/` — those are host-side only and
never run on the device.

## 4. Provide a config file

On first boot, if no `config.json` exists on the device (or it's corrupt),
`Storage` recreates one from the built-in defaults in `src/defaults.py` — the
device boots with Wi-Fi and MQTT disabled until configured.

To configure it upfront instead, create `config.json` with the same shape as
`DEFAULTS` in `src/defaults.py` and fill in at least:

- `wifi.ssid` / `wifi.password`
- `mqtt.server` / `mqtt.port` / `mqtt.user` / `mqtt.password` / `mqtt.base_topic`
  (leave `mqtt.server` empty to disable MQTT entirely)
- `leds.count` / `leds.pin` to match your strip
- `button.pin` / `ir.pin` if wired to non-default GPIOs
- `watchdog.enabled: true` for a deployed device — arms the hardware watchdog
  so the board auto-reboots if the firmware ever hangs (leave it `false` while
  developing; see the [Development guide](development.md#watchdog))

Copy that `config.json` onto the device alongside `main.py`/`src`/`lib`.

`wifi.*` and `mqtt.*` can also be changed later at runtime via the Web API
(the channels reconnect on the spot), but the pin assignments (`leds.pin`,
`button.pin`, `ir.pin`), `watchdog.enabled`, and `leds.on_after_boot` are
only read at boot — changing those means editing the config and rebooting.
See the per-key **Applies** column in the
[Development guide](development.md#top-level-keys).

All runtime state lives in the same file: mode, brightness, speed, and on/off
state are merged into it and autosaved (debounced, atomic write) whenever
they change, so the device resumes where it left off after a power cycle. See
the [Development guide](development.md) for the full list of config keys, how
saving works under the hood, and `config.dev.json` (a git-ignored variant for
local development, so real credentials never end up in the repo).

## 5. First boot

Power the board. Startup order is: load config → start renderer + autosave
task → start all channels concurrently (Wi-Fi, button, MQTT, Web API, IR).
Nothing blocks on Wi-Fi/MQTT connecting — the LED strip lights up immediately
using the persisted mode.

If `logging.enabled` is `true` in the config, log lines are written to the
console appender — watch them over the USB serial REPL.

## 6. Talking to the device

Both the Web API and MQTT wait until Wi-Fi is connected before doing
anything — check `runtime.wifi.connected` if a request or message doesn't
seem to land. For endpoints/topics and payload examples, see:

- [Web API](channels/webapi.md) — JSON over HTTP, `GET`/`POST /json/state`, `GET /info`
- [MQTT](channels/mqtt.md) — topics, retained state, last will

## Developing or extending it

See the [Development guide](development.md) for the architecture, how to set
up a host-side dev environment (lint/test/compile-check), and how to add a
new control method or lighting mode.
