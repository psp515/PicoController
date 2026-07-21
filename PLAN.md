# PicoController v2 — Implementation Plan

Build order for the v2 controller on branch `convtrollev/v2`. Ten steps ordered for
fastest feedback: visible output first, connectivity later. Each step buildable and
testable on its own. Architecture rules live in `.claude/CLAUDE.md`.

## Target file layout

```
src/
  main.py               # entry point: build state, start channels + renderer + heartbeat
  state.py              # BaseState + StateManager
  storage.py            # load/save config.json (atomic, debounced)
  defaults.py           # built-in default config
  renderer.py           # animation loop task, owns the LED strip
  channels/
    base.py             # Channel base class
    wifi.py             # WiFi connectivity channel
    mqtt.py             # mqtt_as client, last will
    webapi.py           # microdot JSON API
    ir.py               # NEC IR receiver
    button.py           # cover push button
  animations/
    base.py             # Animation base class
    registry.py         # MODES dict: name -> class
    off.py
    white.py
    static.py
    rainbow.py
    runner.py
```

## Step 1 — Heartbeat main loop (`src/main.py`)

Smallest possible working program — proves deploy toolchain + asyncio on board.

- Single `uasyncio` event loop on core 0. No `_thread`, no core 1.
- Heartbeat task blinking the onboard LED (`Pin("LED")` on Pico W).
  Slow blink (1 s period) = device alive. Blink patterns can later signal
  status (e.g. fast blink = no WiFi).
- Keep the current skeleton's `sys.path.append("lib")` and
  `asyncio.new_event_loop()` teardown.
- `main()` grows over later steps into: load config, build `StateManager`,
  start channels concurrently (one `asyncio.create_task(channel.start())`
  each), start renderer, await forever.

## Step 2 — Config load + defaults (`src/storage.py`, `src/defaults.py`)

Pulled forward: `main()` needs config to build StateManager. Load side only —
saving comes in Step 9.

- `defaults.py` — built-in default config dict (led count 144, pins, modes,
  "turn LEDs on after power-up" flag, WiFi/MQTT placeholders).
- `storage.load()` — read `config.json` (`config.dev.json` in development).
  Missing or corrupt file: fall back to defaults and recreate the file.

## Step 3 — StateManager (`src/state.py`)

One shared instance, **constructor-injected** — not a module-level singleton.
Created once in `main()`, passed to every channel and the renderer
(`WifiChannel(state)`, `Renderer(state)`). Explicit dependency, trivially
testable on desktop CPython, zero extra cost on MicroPython.

- `BaseState` — read-only device properties every module may need:
  device id (`machine.unique_id()`), app version, board name,
  uptime (`time.ticks_ms()` / `ticks_diff` based). Used for MQTT client id,
  Web API `/info`, etc.
- `StateManager(BaseState)` — holds the config + runtime dict in memory:
  - Dict access: `state["leds"]["count"]` plus a `get(...)` helper.
  - `update(patch)` — merges a partial dict (WLED-style), marks state dirty
    for persistence, then notifies subscribers.
  - `subscribe(callback)` — observer hook. Callbacks are small, synchronous:
    typically just set a flag or `asyncio.Event` (e.g. renderer reloads mode
    next frame). Heavy work never runs inside a callback.

Flow: input channel receives command, calls `state.update(...)`; every other
module reacts through its subscription. No input path touches the strip or
renderer directly.

## Step 4 — Renderer + first modes (`src/renderer.py`, `src/animations/`)

Before any channel: visible LED output proves the whole state-observer flow
with hardcoded state changes.

- `animations/base.py` — `Animation`:
  - `__init__(self, params)`.
  - `render(self, buffer, frame)` — fills the preallocated `bytearray`.
  - `interval_ms` — per-mode frame delay.
- Start with two modes only: `off.py`, `static.py` (static color).
- `animations/registry.py` — `MODES = {"off": Off, "static": Static}`.
  Adding a mode = new file + one dict entry. Core loop untouched.
- `renderer.py` — the only module talking to the strip (WS2812B, GP0):
  - One preallocated `bytearray` pixel buffer, reused every frame.
  - Loop: instantiate mode from `MODES` with params from state, call
    `render()`, write buffer, `await asyncio.sleep_ms(interval)`.
  - Subscribes to state; on mode/param change swaps animation next frame.
  - Timing only via `time.ticks_ms()` / `time.ticks_diff()`.

## Step 5 — Channel abstraction + button (`src/channels/base.py`, `button.py`)

Button first: cheapest real input, validates channel abstraction and command
flow end-to-end without network debugging.

- `base.py` — `Channel`:
  - `__init__(self, state)` — gets the shared `StateManager`.
  - `async def start(self)` — runs as its own task.
  - `async def stop(self)`.
  - `name` property.
- `button.py` — GP3, active low, internal pull-up, software debounce.
  Short press cycles modes via `state.update(...)`.

## Step 6 — WiFi channel (`src/channels/wifi.py`)

- STA mode connect using credentials from state.
- Retry/reconnect loop with backoff.
- Publishes status via `state.update({"runtime": {"wifi": ...}})` so
  dependent channels (MQTT) react through subscription.

## Step 7 — MQTT + Web API channels (`src/channels/mqtt.py`, `webapi.py`)

- `mqtt.py` — `mqtt_as`, waits for WiFi status, registers last-will message
  posted to broker on power-off.
- `webapi.py` — microdot as uasyncio task, `GET /json/state` + partial
  `POST` updates (WLED-style). API module kept separate from future WebUI
  serving.

## Step 8 — Remaining animations (`src/animations/`)

Pure additions, no core changes: `white.py`, `rainbow.py`, `runner.py`
(few LEDs running around the strip). Register each in `MODES`.

## Step 9 — Persistence save side (`src/storage.py`)

- `save()` — write temp file, then `os.rename()` (atomic, no corruption on
  power loss mid-write).
- **Debounced**: `StateManager.update()` only sets a dirty flag; a storage task
  saves ~2 s after the last change. Never write flash per frame or per slider
  tick.
- Runtime state (current mode, mode params, brightness) persists too, so a
  power cycle restores the previous look; respects the
  "turn LEDs on after power-up" option.

## Step 10 — IR channel (`src/channels/ir.py`)

- GP2, pin IRQ records edge timestamps only — ISR never allocates, prints,
  or decodes.
- NEC decoding in a uasyncio task (Peter Hinch `micropython_ir` pattern).
- Decoded commands feed `state.update(...)` like every other channel.
