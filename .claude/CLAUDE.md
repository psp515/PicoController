# Project

It is a MicroPython ARGB LED Controller.

## Requirements

### Current

- primarly it is designed to handle WS2812B LED 5V
- Available communication protocols for configuration
    - NEC Reveiver
    - Button on the cover
    - MQTT Protocol
    - Web API 
- Controller Mircopython code should be as simple as possible to understand without complex elements
    - for that aplication might use python abstractions to abtract elements like modes communications and so on
- Controller should support multiple Animation Modes and animations should be easilly extensible
- Configuration should be dynamic - device reflects changes after hitting save on webui or after api call 
- Configuration should be presited between on and off in .json file (also runtime data like current mode and mode specs)
- if device will be turned off there should be posted message to mqtt broker about last will
- provide option whether to tunr on led after powering up 

### Future directions

If introducing helpfull abstraction will not be problematic it is advised to apply this abstraction.
- Controller might be extended with Web UI
- in future there will be more like WS2811 LED 12V support

### Selected Libraries 

- for mircopython connection use mqtt_as
- uasyncio for main loop 

## Hardware 

### Current

- Board: Raspberry Pi Pico W
- WS2812B data line: GP0 
- Optional - IR receiver (NEC protocol, remote control): GP2, interrupt-driven
- Optional - Push button (on cover): GP3, active low, internal pull-up, debounced in software
- LED count: 144 default, configurable in `config.json`

### Future directions

- Board: ESP32

## Architecture rules

- Single `uasyncio` event loop on core 0. Do NOT use `_thread` or core 1.
- Animation modes live in `src/animations/`, one class/function per mode, registered in
  a mode table (dict/list). Adding a new animation must not require touching the core loop.
- IR receiver: pin IRQ records edge timestamps only. ISRs must not allocate memory,
  print, or decode. NEC decoding happens later in a uasyncio task
  (pattern: Peter Hinch `micropython_ir`).
- All inputs (IR, button, MQTT, Web API) translate into the same command/event
  objects feeding one shared application state. No input path talks to the LED
  strip or renderer directly. State Manager class manages channels 
- Communication channels (MQTT, Web API, IR, button) are abstracted behind a common
  interface so new channels can be added without changing core logic. (`src/channels/`)
- Application should start as quickly as possible and cahnnels should start concurrenctly

## Selected libraries

- `uasyncio` — main loop and all tasks
- `mqtt_as` (Peter Hinch, micropython-mqtt) — async, resilient MQTT client
- `micropython_ir` (Peter Hinch) — NEC IR decoding
- Do not add other dependencies without asking. Never use blocking `umqtt.simple`/`umqtt.robust`.

## Configuration

- Persisted in `config.json` on the device filesystem; includes runtime state
  (current mode, mode parameters, brightness) so state survives power cycles.
- for development `config.dev.json` should be used 
- Changes are dynamic: applying config via Web API or WebUI "save" takes effect
  immediately, no reboot.
- Writes: temp file + `os.rename()` (atomic, protects against corruption).
- Debounce/batch saves — never write flash per frame or per slider tick.
- Missing or corrupt file → fall back to built-in defaults and recreate the file.

## Web API

- Async HTTP server (e.g. microdot) as a uasyncio task; JSON request/response.
- Endpoints modeled after WLED's `/json/state` idea: GET state, POST partial updates.
- Future: static WebUI served by the same server; keep API and UI serving separate modules.

## MicroPython constraints

- This is MicroPython, not CPython: no `typing` at runtime, no heavy stdlib imports.
- Avoid per-frame heap allocations — reuse preallocated `bytearray` pixel buffers.
- Use `time.ticks_ms()` / `time.ticks_diff()` for timing, never naive subtraction.
- Use `micropython.const()` for constants; keep modules small (RAM limits).
- No busy-wait `time.sleep()` inside tasks — always `await asyncio.sleep_ms()`.

## Code style

- Simple to understand. Prefer plain classes and dicts over
  metaprogramming, decorators-heavy designs, or deep inheritance.
- Introduce an abstraction only when it clearly helps extensibility
  (animations, comm channels, LED drivers) — otherwise keep it flat.
- Don't comment 

## Session-specific guidance

- Skills are stored in `.claude/skills/` in this repo (tracked in git) so they
  persist across machines via GitHub instead of only living in the global
  `~/.claude` config.
- Invoke the `caveman` skill at the start of every chat in this project by
  default, no trigger phrase needed. Keep it active per its own persistence
  rules (stays on until user says "stop caveman" / "normal mode").
- Don't remove added comments by developers - they will start with U 