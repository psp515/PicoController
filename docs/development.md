---
layout: default
title: Development
nav_order: 3
---

# Development guide

This page is for anyone changing the code: 
- how the device works internally,
- how to set up a host-side dev environment
- how the config file is structured. 
- If you just want to run the device, see [Manual setup](setup.md) instead.

## How it works

```
IR / Button / MQTT / Web API  ──►  StateManager  ──►  Renderer  ──►  WS2812B strip
        (channels)                 (shared state)      (animations)
                                        │
                                        ▼
                                   config.json
                              (debounced autosave)
```

Everything runs in a single `uasyncio` event loop on one core. At boot,
`main.py` loads the config, then starts the renderer, the autosave task, and
every channel (Wi-Fi, button, MQTT, Web API, IR) concurrently as independent
tasks — nothing blocks waiting on anything else, so the strip lights up
immediately using whatever was last saved.

Every input path (a "channel") is just a translator: it turns "the user did
something" — a button press, an IR code, an MQTT message, an HTTP request —
into a small JSON patch applied to one shared application state. The renderer
watches that same state and redraws the strip whenever it changes. No input
path ever touches the LED strip directly, and the renderer never knows or
cares which channel triggered a change.

## Architecture

- **`StateManager`** (`src/state.py`) holds the entire config + runtime state
  as a plain dict, with a small `Mode` helper for the frequently-read fields
  (`current`, `brightness`, `speed`, `on`). `update(patch)` merges a patch in,
  validates/clamps mode fields (e.g. brightness/speed are clamped to 1-100),
  persists it (debounced), and notifies subscribers — including the renderer.
- **Channels** (`src/channels/`) are the only things allowed to call
  `state.update(...)`. See [Channels](channels/index.md) for the interface and
  how to add a new one.
- **Renderer** (`src/renderer.py`) watches the state for changes, instantiates
  the active animation from a mode registry, and renders it into a
  preallocated NeoPixel buffer every frame, applying global brightness
  scaling. See [Animations](animations/index.md) for the interface and how to
  add a new mode.
- **Storage** (`src/storage.py`) loads the config file on boot, merging over
  built-in defaults, and autosaves changes back with a debounce + atomic
  `os.rename()` write. Details below.
- **Logger** (`src/logger/`) is config-driven and disabled by default;
  application code never calls `print()` — see the `Logger` class and its
  appenders (`ConsoleAppender`, with a file appender planned).

## Setting up a development environment

The `src/` code is written so the pure-logic parts (`state.py`, `storage.py`,
`defaults.py`, and channels that don't touch hardware) also import and run
unchanged on regular CPython — that's what the test suite exercises. Code
that touches hardware (`machine`, `network`, `neopixel`, `microdot`) only runs
on-device; `tests/conftest.py` stubs the handful of MicroPython-only modules
and functions (`mqtt_as`, `machine` incl. `Pin`, `neopixel`,
`time.ticks_ms`/`ticks_diff`, `asyncio.sleep_ms`) needed to import
`channels/mqtt.py` and `renderer.py` under test.

Install once:

```
pip install ruff pytest
```

Then, matching `.github/workflows/ci.yml` (lint → build → test):

- Lint: `python -m ruff check src main.py`
- Compile-check (syntax only, all source files): `python -m compileall -q src main.py`
- Tests: `python -m pytest` (`pythonpath` is `src`, configured in `pyproject.toml`; tests live in `tests/`)

To actually try a change on hardware, copy the edited files onto the device
as described in [Manual setup](setup.md) — there's no build step in between.

### Libraries in use

- `uasyncio` — the only concurrency model; no `_thread`, no second core.
- `mqtt_as` (Peter Hinch, micropython-mqtt) — async, resilient MQTT client.
- `micropython_ir` (Peter Hinch) — NEC IR decoding.
- `microdot` — the async HTTP server behind the Web API.

### MicroPython constraints to keep in mind

- No `typing` at runtime, no heavy stdlib imports.
- Avoid per-frame heap allocations — reuse preallocated `bytearray`/buffer
  objects (see how animations write into the renderer's buffer).
- Use `time.ticks_ms()`/`time.ticks_diff()` for timing, never naive
  subtraction (`time.ticks_ms()` wraps around).
- No busy-wait `time.sleep()` inside tasks — always `await asyncio.sleep_ms()`.
- Keep modules small and prefer plain classes/dicts over metaprogramming or
  deep inheritance — this codebase is meant to stay easy to read.

## Configuration file

All configuration and runtime state lives in one JSON file, loaded by
`Storage` (`src/storage.py`) at boot and merged over the built-in `DEFAULTS`
(`src/defaults.py`), so a partial or older config still works — missing keys
just fall back to their default.

### `config.json` vs `config.dev.json`

`Storage` prefers `config.dev.json` over `config.json` if both exist on the
filesystem. `config.dev.json` is listed in `.gitignore` — it exists so you can
keep a filled-in set of real Wi-Fi/MQTT credentials on your machine for local
development without ever committing secrets to the repo. Use only one of the
two on an actual device — see [Manual setup](setup.md) for setting up
`config.json` there.

### How saves work

- Every change goes through `StateManager.update(...)`, which merges the
  patch into memory immediately (the strip reacts right away) and marks the
  state as changed.
- A background task (`Storage.autosave`) waits for that change, then keeps
  waiting in ~2s slices as long as more changes keep arriving, so rapid
  changes (e.g. dragging a brightness slider) are batched into a single
  write instead of hitting flash on every tick.
- Writes go to `config.json.tmp` then `os.rename()` over the real file — an
  atomic swap, so a power loss mid-write can't corrupt the config.
- The `runtime` key (e.g. `runtime.wifi.connected`) is excluded from what
  gets persisted — it's live status, not configuration.
- If the file is missing or fails to parse as JSON, `Storage` falls back to
  `DEFAULTS` and immediately recreates the file.

### Top-level keys

| Key | Fields | Notes |
|---|---|---|
| `device` | `name` | Display name only |
| `leds` | `count`, `pin`, `on_after_boot`, `segmenting` | `count`/`pin` describe the physical strip; `on_after_boot` controls whether it lights up on power-up or waits `off`; `segmenting: {"enabled": bool, "length": n}` splits the strip into repeating `length`-LED blocks for compatible modes — see [Animations](animations/index.md#segmenting) |
| `mode` | `current`, `brightness`, `speed`, `on` | Runtime mode state: active mode name, global brightness/speed (1-100, clamped), and on/off |
| `modes` | one entry per mode name | Each mode's own params, e.g. `static: {"color": [r, g, b]}`, `runner: {"color": [...], "length": n}` — see [Animations](animations/index.md) |
| `wifi` | `ssid`, `password` | Empty `ssid` disables Wi-Fi (and everything that depends on it) |
| `mqtt` | `server`, `port`, `user`, `password`, `base_topic`, `ssl`, `ssl_params`, `ntp_host` | Empty `server` disables MQTT entirely; `ssl: true` also triggers an NTP time sync (needed for TLS) before connecting |
| `button` | `pin` | GPIO for the cover button |
| `ir` | `pin`, `codes` | GPIO for the IR receiver; `codes` maps received NEC codes to arbitrary state patches |
| `logging` | `enabled`, `level` | Disabled by default; `level` is one of `debug`/`info`/`warning`/`error` |
| `watchdog` | `enabled` | Hardware watchdog (see below); disabled by default, enable on production devices |

`runtime` is a further top-level key that appears once the device is running
(e.g. `runtime.wifi.connected`/`ip`) — it's written by channels, read like any
other state, but never persisted to disk.

## Watchdog

With `watchdog.enabled: true`, the heartbeat task in `main.py` arms the
RP2040's hardware watchdog (`machine.WDT`, 8s timeout — the hardware maximum
is ~8.3s) and feeds it every 500ms while toggling the onboard LED. If the
event loop ever stalls — a blocking call that never returns, a crashed
scheduler, wedged Wi-Fi chip state — the feed stops and the chip hard-resets
itself within 8 seconds, so a deployed device self-heals instead of hanging
until someone pulls the plug.

Things to keep in mind:

- **Keep it off during development** (`config.dev.json` sets
  `"watchdog": {"enabled": false}`). The RP2040 watchdog cannot be disarmed
  once started — dropping to the REPL (Ctrl-C) stops the heartbeat, so an
  armed watchdog reboots the board out from under your session 8s later.
- Any single synchronous operation on the event loop must finish well under
  the 8s timeout — flash writes and `gc.collect()` are comfortably inside
  that, but it's another reason every network call must have a bounded
  timeout (see the NTP sync in `src/channels/mqtt.py`).
- A watchdog reset looks like a power cycle: the device reboots cleanly,
  reloads `config.json`, and resumes the persisted mode. The MQTT broker
  publishes the last-will `"offline"` message if a session was up.

## Extending the device

- [Channels](channels/index.md) — add a new way to control the device (a
  new input path)
- [Animations](animations/index.md) — add a new lighting mode
