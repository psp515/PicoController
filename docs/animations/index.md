---
layout: default
title: Animations
nav_order: 5
---

# Animations

An **animation** is one lighting mode — `off`, `white`, `static`, `rainbow`,
`runner`. The `Renderer` (`src/renderer.py`) owns a single `uasyncio` loop that
picks the active animation, calls its `render()` once per frame, and writes
the result to the NeoPixel strip. Modes never touch `neopixel`/hardware
themselves; each mode is responsible for applying brightness itself (see
`apply_brightness` below).

## The `Animation` interface

Defined in `src/animations/base.py`:

```python
class Animation:
    interval_ms = 40
    segmenting_compatible = True

    def __init__(self, mode, params):
        self.mode = mode
        self.params = params

    def render(self, buffer, count, frame):
        pass

    def apply_brightness(self, buffer, count):
        ...
```

- `interval_ms` — delay between frames; the renderer sleeps this long after
  each `render()` call. Override per-class, or compute dynamically in
  `__init__` from `mode.speed` (see `Runner`).
- `segmenting_compatible` — whether this mode may be split into repeating
  `leds.segmenting.length`-LED blocks when segmenting is enabled; see
  [Segmenting](#segmenting) below. Defaults to `True`; override to `False` for
  modes where segmenting wouldn't change anything (a solid fill) or wouldn't
  make sense (a single trail chasing the whole strip).
- `mode` — the shared `Mode` helper (`src/state.py`), giving read access to
  `mode.current` / `mode.brightness` / `mode.speed` / `mode.on`.
- `params` — this mode's own config dict, e.g. `{"color": [255, 120, 30]}` for
  `static`, read from `modes.<name>` in the config.
- `render(buffer, count, frame)` — called every frame; must write `count`
  pixels into `buffer` and return nothing. `frame` is a monotonically
  increasing counter, reset to `0` whenever the mode (re)loads. When
  segmenting is active, `count` here is the *segment* length, not the full
  strip — see [Segmenting](#segmenting).
- `apply_brightness(buffer, count)` — scales the whole buffer down by
  `mode.brightness` (1-100) in place. Call this yourself as the last line of
  `render()` once you've written raw colors. `off` is the one built-in
  exception: it fades an already-captured snapshot down to black and is
  producing final output values directly, so it doesn't call it.

### Buffer format

`buffer` is the NeoPixel driver's raw byte buffer, laid out **G, R, B** per
pixel (MicroPython's `neopixel` module default order) — that's `count * 3`
bytes. Write it directly rather than allocating a new buffer/list per frame;
none of the built-in animations allocate inside `render()` except lazily
once (see `Runner`'s cached `_zeros`).

## Built-in modes

Registered in `src/animations/registry.py`:

| Mode | File | Params | Segmenting | Notes |
|---|---|---|---|---|
| `off` | `off.py` | `fade_ms` (default `600`) | No | Fades whatever was last displayed down to black over `fade_ms`, using an eased (quadratic) curve, then holds all pixels off. Entered whenever `mode.on` is `False` or an unknown mode is selected. |
| `white` | `white.py` | — | No | Full white, `interval_ms=500` (static image, no need to redraw fast) |
| `static` | `static.py` | `color: [r, g, b]` | No | Solid color |
| `rainbow` | `rainbow.py` | — | **Yes** | Precomputes a 256-step color wheel once; scrolls it using `mode.speed` |
| `runner` | `runner.py` | `color: [r, g, b]`, `length` | No | Trail of `length` pixels chasing around the strip; `interval_ms` derived from `mode.speed` |

`off`/`white`/`static` opt out because segmenting a solid fill produces the
exact same output as rendering it across the whole strip — there's nothing to
tile. `runner` opts out because its trail is meant to travel the full strip;
confined to a short segment its `length` param usually exceeds the segment
size, so it degenerates into a solid block that repeats rather than a visible
chase — see [Segmenting](#segmenting).

## Segmenting

Splits the strip into repeating `leds.segmenting.length`-LED blocks so a
compatible mode's pattern repeats every N LEDs instead of stretching across
the whole strip once. Configured under `leds.segmenting` in the config
(`src/defaults.py`):

```json
"segmenting": {"enabled": false, "length": 2}
```

- **Only applies to modes with `segmenting_compatible = True`** (see the
  table above) — incompatible modes always render across the full strip,
  regardless of this config.
- **`length` has a floor of 2**, enforced in `StateManager.update()`
  (`src/state.py`) the same way `mode.brightness`/`speed` are clamped.
- **No ceiling is enforced at write time.** If `length` ends up `>= leds.count`
  (e.g. you shrink `count` after setting a large segment), the `Renderer`
  falls back to rendering the full strip as one segment — this is
  re-evaluated fresh every frame (`Renderer._segment_count`,
  `src/renderer.py`), so it self-heals regardless of which value changed or
  in which order.
- **Rendering**: the active animation's `render()` is called once with
  `count` set to the segment length, producing one segment's worth of
  pixels; `Renderer._tile()` then copies that segment across the rest of the
  buffer. If `leds.count` isn't a multiple of `length`, the final repeat is
  **truncated mid-pattern** rather than scaled down — e.g. `count=23`,
  `length=5` renders 4 full 5-LED segments plus a 5th segment cut off after
  its first 3 LEDs.
- **Overridable via MQTT** the same way `mode` fields are — see
  [MQTT channel](../channels/mqtt.md#311-allow-list-for-the-update-topic).

## Adding a new mode

Nothing else needs to change: selecting `mode.current = "<name>"` (via any
channel) makes the renderer pick it up automatically. Steps:

1. Create `src/animations/<name>.py` from the template below.
2. Register it in the `MODES` dict in `src/animations/registry.py`.
3. Add a default params entry under `modes.<name>` in `DEFAULTS`
   (`src/defaults.py`) and in `config.dev.json`, even if it's just `{}`.

### Template

```python
from animations.base import Animation


class MyMode(Animation):
    interval_ms = 40  # ms between frames; override or compute from mode.speed

    def __init__(self, mode, params):
        super().__init__(mode, params)
        color = params.get("color", [255, 255, 255])
        self._r = color[0]
        self._g = color[1]
        self._b = color[2]

    def render(self, buffer, count, frame):
        for i in range(0, count * 3, 3):
            buffer[i] = self._g      # buffer order is G, R, B
            buffer[i + 1] = self._r
            buffer[i + 2] = self._b
        self.apply_brightness(buffer, count)
```

### Rules to follow

- Don't allocate new buffers/lists inside `render()` — it runs every frame.
  Precompute lookup tables etc. in `__init__` (see `Rainbow`'s color wheel),
  and if you need a scratch buffer, allocate it once and cache it (see
  `Runner`'s `_zeros`).
- Call `self.apply_brightness(buffer, count)` as the last line of `render()`
  once you've written raw colors — it's not automatic. Skip it only if your
  mode is producing final, already-scaled output directly (see `off`).
- Read `mode.speed` / `params` defensively with `.get(...)` and a default;
  clamp anything that could be `0` or negative before using it as a divisor
  (see `Rainbow`/`Runner` clamping `speed` to at least `1`).
- Keep `render()` allocation-free and branch-light — it runs on a
  memory-constrained MicroPython board, once per `interval_ms`.

### Registering it

```python
# src/animations/registry.py
from animations.mymode import MyMode

MODES = {
    "off": Off,
    "white": White,
    "static": Static,
    "rainbow": Rainbow,
    "runner": Runner,
    "mymode": MyMode,
}
```

```python
# src/defaults.py
"modes": {
    ...
    "mymode": {"color": [255, 0, 0]},
},
```
