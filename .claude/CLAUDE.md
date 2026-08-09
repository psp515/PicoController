# Project

It is a MicroPython ARGB LED Controller.

## Requirements

### Current

- primarly it is designed to handle WS2812B LED 5V
- Available communication protocols for configuration
  - NEC Reveiver
  - Button on the cover
  - MQTT Protocol
  - Web API + a browser Web UI (dashboard + full-config page) served by the
    device itself
- If the configured Wi-Fi network is empty or unreachable, the device falls
  back to its own temporary access point so the Web UI is always reachable
  to fix credentials — see [Configuration](#configuration) and
  `docs/channels/wifi.md`
- Controller Mircopython code should be as simple as possible to understand without complex elements
  - for that aplication might use python abstractions to abtract elements like modes communications and so on
- Controller should support multiple Animation Modes and animations should be easilly extensible
- Configuration should be dynamic - device reflects changes after hitting save on webui or after api call 
- Configuration should be presited between on and off in .json file (also runtime data like current mode and mode specs)
- if device will be turned off there should be posted message to mqtt broker about last will
- provide option whether to tunr on led after powering up 
- lightinginh modes:
  - white mode
  - static color mode
  - rainbow effect
  - running few leds around the LEDS
- on / off function for device LEDS

### Future directions

If introducing helpfull abstraction will not be problematic it is advised to apply this abstraction.
- in future there will be more like WS2811 LED 12V support
- introducing more modes 

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
- The Wi-Fi channel is the radio's single owner — both `STA_IF` and `AP_IF`.
  No other code drives either interface — mqtt uses `ExternalWifiMQTTClient`
  (subclass in `src/channels/mqtt.py`) so `mqtt_as` never connects/disconnects
  Wi-Fi itself, it only waits for the radio to be up. The AP is a fallback
  only, never run concurrently with an active station connection (shared
  single-radio channel constraints) — see `docs/contributing/channels.md`.
- The Web API channel keeps JSON API routes (`src/channels/webapi.py`) and
  static Web UI routes (`src/webui.py`) in separate modules sharing one
  `Microdot` app/port, so either can change without touching the other.
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
  immediately, no reboot. This includes `wifi.*` (channel reconnects; reverts
  to last-known-good credentials if the new ones never connect) and `mqtt.*`
  (channel tears the session down, publishes `offline` on the old topic, and
  reconnects with the new config).
- Boot-only exceptions: pin assignments (`leds.pin`, `button.pin`, `ir.pin` —
  pin changes imply rewiring, reboot is free), `watchdog.enabled` (RP2040 WDT
  can't be disarmed once armed), `leds.on_after_boot` (boot-only by nature).
- Every channel except wifi has an `enabled` flag (`mqtt.enabled`,
  `webapi.enabled`, `button.enabled`, `ir.enabled`, default true, dynamic):
  disabled channels skip their work loop and just sleep/wait. Wifi's
  "disabled" state is an empty `ssid`; a disabled wifi also disables mqtt
  (mqtt requires non-empty `wifi.ssid`). Empty `ssid`, and a configured
  network the device can't reach after a few tries, both fall back to the
  same temporary access point (`wifi.ap_ssid`/`wifi.ap_password`) rather than
  idling — the Web UI stays reachable either way.
- Every config key must be documented in the docs config tables — the
  user channel page's "Settings" table and/or the "Top-level keys"
  table in `docs/development.md` — with its default and what it's used for.
  The "Top-level keys" table (developer reference) also carries an
  **Applies** column stating whether a change takes effect live or requires
  a reboot. Adding or changing a config key means updating those tables in
  the same change.
- Writes: temp file + `os.rename()` (atomic, protects against corruption).
- Debounce/batch saves — never write flash per frame or per slider tick.
- Missing or corrupt file → fall back to built-in defaults and recreate the file.
- for quick acces keep dict in memory so fields can be easily accessible via `state["value1"]["value2"]`

## Logging

- Use the `Logger` class from `src/logger/` (injected via constructor), never `print()`
  in application code — output goes through appenders (`ConsoleAppender`, future file appender).
- Config-driven via the `logging` config section; disabled by default.
- Message parameters use positional placeholders, formatted lazily (skipped when disabled):
  `logger.info("wifi", "connected ip {0}", ip)` — no f-strings, no named `{value}` kwargs.

## Web API

- Async HTTP server (e.g. microdot) as a uasyncio task; JSON request/response.
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

## Planning work (IMPORTANT)

When planning any task (plan mode, a todo list, or a multi-step change),
structure the plan as a sequence of **small steps**, each independently
verifiable. Never plan one big "implement everything, then test" step.

Each step follows this cycle:

1. **Add the test first, when possible** — if the new behavior can be
   expressed as a test before the code exists (new function, new validation
   rule, new channel behavior), write the failing test first, then make it
   pass. If a test-first approach isn't practical (e.g. hardware-bound code
   needing new stubs, large refactors), write the test in the same step,
   immediately after the change — never defer tests to a later step.
2. **Make one small code change** — one behavior, one module, one concern.
3. **Check tests** — run `python -m pytest` (plus `python -m ruff check src
   main.py` and `python -m compileall -q src main.py`) after every step, not
   only at the end.
4. **Fix failures before moving on** — a step is done only when lint,
   compile-check, and tests are green. Don't start the next step on top of a
   red suite.

Steps should be small enough that a failure clearly points at the change
that caused it. Docs/CLAUDE.md updates required by the change (see
[Keeping this file and the docs in sync](#keeping-this-file-and-the-docs-in-sync))
are part of the plan too — as their own step, in the same change.

## Development

Mirrors `.github/workflows/ci.yml` (lint → build → test), runs on CPython, not on-device.

- Lint: `python -m ruff check src main.py`
- Compile-check (syntax only, all source files): `python -m compileall -q src main.py`
- Tests: `python -m pytest` (pythonpath is `src` and `lib`, configured in `pyproject.toml`; tests live in `tests/`)
- Always invoke tools via `python -m` (`ruff`, `pytest`) — bare executables are not on PATH here.

## Documentation (GitHub Pages)

- Docs live in `docs/`, built by Jekyll with the `just-the-docs` theme via
  `remote_theme: just-the-docs/just-the-docs@v0.10.1` in `docs/_config.yml`
  (pinned tag — bump deliberately). Published by GitHub Pages from the
  `docs/` folder (deploy from branch).
- Local preview (needs Ruby + bundler; `docs/Gemfile` pins the `github-pages` gem):
  ```
  cd docs
  bundle install
  bundle exec jekyll serve --livereload
  ```
  then open http://localhost:4000. First build needs network (remote theme download).
- Navigation is generated from page front matter: `title` + `nav_order` for
  top-level pages; section index pages set `has_children: true`; child pages
  set `parent: <section title>`. New doc page = add front matter, nav updates
  itself.
- Theming: stock just-the-docs, no overrides. `color_scheme: dark` in
  `docs/_config.yml` selects the theme's built-in dark scheme — no
  `docs/_sass/` or `docs/_includes/` customization.

## Session-specific guidance

- Skills are stored in `.claude/skills/` in this repo (tracked in git) so they
  persist across machines via GitHub instead of only living in the global
  `~/.claude` config.
- Invoke the `caveman` skill at the start of every chat in this project by
  default, no trigger phrase needed. Keep it active per its own persistence
  rules (stays on until user says "stop caveman" / "normal mode").
- Don't remove added comments by developers - they will start with U

## Keeping this file and the docs in sync

Whenever a change affects something described in this file or in `docs/` —
a new/changed config field, a new mode or channel, a new architecture rule,
a behavior change (e.g. what's now dynamically updatable, what gets
validated, what a channel exposes) — update both **in the same change**,
not as a follow-up:

- Update the relevant section of this file (`.claude/CLAUDE.md`) if the
  change affects a requirement, architecture rule, or convention stated
  here.
- The docs are split into two tracks and changes must respect it:
  **user-facing** pages (`index.md`, `setup.md`, `channels/*.md`,
  `animations/index.md`) explain use, configuration and behavior in plain
  language, with **no implementation details** (no internal method names,
  constants, or code walkthroughs); **developer** pages under Contributing
  (`development.md`, `contributing/index.md`, `contributing/channels.md`,
  `contributing/animations.md`) hold the architecture and all internals.
  Put user-visible behavior on the user page, implementation on the
  Contributing page, and cross-link between them.
- Update the relevant page(s) under `docs/` — see
  [Documentation (GitHub Pages)](#documentation-github-pages) above for how
  navigation/front matter works when adding a new page.
- If a change only affects internal implementation with no user- or
  contributor-visible behavior change, no doc update is needed — don't pad
  docs with internal detail no one reading them would act on.
