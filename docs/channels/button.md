---
layout: default
title: Button channel
parent: Channels
nav_order: 2
---

# Button channel

Implemented in `src/channels/button.py`. Polls a single push button on the
cover and turns short/long presses into state patches — no library, no
interrupts, just a debounced poll loop.

## What you can do with it

The button on the cover is the whole no-phone, no-network interface — two
gestures, one button:

| Device is | You do | What happens |
|---|---|---|
| Off | **Click** (short press) | Lights turn **on**, resuming the last mode |
| On | **Click** (short press) | Switches to the **next lighting mode** |
| On | **Hold ~1s**, release | Lights turn **off** |
| Off | **Hold ~1s**, release | Lights turn **on** |
| Any | **Hold longer than ~2s** | Nothing — press is cancelled, guards against accidental holds |

So: click to wake it or change the look, hold briefly to switch it off.
Everything the button changes is saved automatically — after a power cut the
device comes back exactly as you left it. The rest of this page is the
technical detail behind those two gestures.

## 1. Debounced poll loop, three outcomes

The pin is read every `POLL_MS`; a level only "counts" once it's been stable
for `STABLE_POLLS` consecutive polls, which filters out mechanical bounce
without any hardware debounce circuit. What happens next depends on how long
the button was held between the debounced press and the debounced release.

### Constraints for it to work

- **Active low, internal pull-up.** `Pin(pin_no, Pin.IN, Pin.PULL_UP)` — the
  pin reads `1` at rest and `0` while pressed, matching a button wired to
  ground.
- **Debounce is time-based, not edge-based.** A raw level change resets the
  stability counter (`count = 0`); only after `STABLE_POLLS` polls in a row
  agree on the new level does it become the accepted `stable` value.
- **Timing is measured on release, not on press.** `pressed_at` is recorded
  on the debounced falling edge; the action taken is decided on the
  debounced rising edge, from `held_ms = ticks_diff(now, pressed_at)`.
- **No ISR.** Unlike the IR receiver, a button doesn't need microsecond edge
  capture, so a plain `asyncio.sleep_ms(POLL_MS)` poll loop is simple enough
  and matches the project's "as simple as possible" rule.

### 1.1 Basic workflow

`start()` runs for the lifetime of the device, polling every `POLL_MS`:

1. Debounce the raw pin level against `STABLE_POLLS`.
2. On a debounced **press** (level goes to `0`): record `pressed_at`.
3. On a debounced **release** (level goes back to `1`), classify `held_ms`:
   - `>= ABORT_MS`: held far too long, treated as an aborted gesture — no
     state change, just a log line.
   - `>= LONG_PRESS_MS`: toggles `mode.on` (device on/off).
   - otherwise (**short press**):
     - if the device is currently **off** (`mode.on` is `false`), turn it
       **on** — the press is consumed by waking the device, it does not
       also advance the mode.
     - if the device is already **on**, advance to the next mode via
       `state.mode.next_mode()`.

So from off, the first short press only turns the device on; only presses
after that cycle through modes. This mirrors how most remotes behave: a
"power" gesture and a "next" gesture are the same physical action, but the
device only ever does one of them per press.

### 1.2 Used configuration

Read from the `button` section of `config.json` (defaults in
`src/defaults.py`):

| Config key | Default | Used for | Applies |
|---|---|---|---|
| `button.pin` | `3` | GPIO pin the button is wired to (active low, internal pull-up) | reboot required |
| `button.enabled` | `true` | `false` makes the channel ignore the button entirely — the loop just sleeps (`DISABLED_POLL_MS`) instead of polling the pin | live — picked up within one `DISABLED_POLL_MS` (1 s) |

The press-timing thresholds (`POLL_MS`, `STABLE_POLLS`, `LONG_PRESS_MS`,
`ABORT_MS`) are module constants in `src/channels/button.py`, not config —
change them there and re-flash if the physical button needs different
timing. To move the button to a different pin, set `button.pin` in
`config.json` (or `config.dev.json`) and reboot — the pin is bound once at
startup. Deliberate: moving a button means rewiring hardware anyway, so a
reboot costs nothing, and a live pin swap would only add teardown
complexity. The same applies to `ir.pin` and `leds.pin`.

## 2. Exposed functions

`ButtonChannel` (`src/channels/button.py`) implements the standard
[`Channel`](index.md) interface; all of the press-classification logic in
[1.1](#11-basic-workflow) runs inline inside `start()` rather than being
split into helpers:

| Function | Type | What it does |
|---|---|---|
| `start()` | `Channel` interface | Runs the debounce/classify loop in [1.1](#11-basic-workflow); the device's single long-lived entry point for this channel |
| `stop()` | `Channel` interface | Stops the poll loop |
