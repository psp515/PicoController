function rgbToHex(rgb) {
  return "#" + rgb.map((c) => c.toString(16).padStart(2, "0")).join("");
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function getPath(obj, path) {
  return path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

function setPath(obj, path, value) {
  const keys = path.split(".");
  let node = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    node[keys[i]] = node[keys[i]] || {};
    node = node[keys[i]];
  }
  node[keys[keys.length - 1]] = value;
}

function debounce(fn, ms) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

function fetchState() {
  return fetch("/json/state").then((r) => r.json());
}

function postPatch(patch) {
  return fetch("/json/state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  }).then((r) => r.json());
}

function showBanner(text) {
  const banner = document.getElementById("banner");
  if (!banner) return;
  banner.textContent = text;
  banner.hidden = false;
  clearTimeout(showBanner._timer);
  showBanner._timer = setTimeout(() => {
    banner.hidden = true;
  }, 2500);
}

const debouncedPatch = debounce(postPatch, 300);

function initDashboard(state) {
  document.getElementById("device-name").textContent = state.device.name;

  const modeSelect = document.getElementById("mode-current");
  Object.keys(state.modes)
    .filter((name) => name !== "off")
    .sort()
    .forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      modeSelect.appendChild(opt);
    });
  modeSelect.value = state.mode.current;
  modeSelect.addEventListener("change", () => {
    postPatch({ mode: { current: modeSelect.value } });
  });

  const onToggle = document.getElementById("mode-on");
  onToggle.checked = state.mode.on;
  onToggle.addEventListener("change", () => {
    postPatch({ mode: { on: onToggle.checked } });
  });

  const brightness = document.getElementById("mode-brightness");
  const brightnessValue = document.getElementById("brightness-value");
  brightness.value = state.mode.brightness;
  brightnessValue.textContent = state.mode.brightness;
  brightness.addEventListener("input", () => {
    brightnessValue.textContent = brightness.value;
    debouncedPatch({ mode: { brightness: Number(brightness.value) } });
  });

  const speed = document.getElementById("mode-speed");
  const speedValue = document.getElementById("speed-value");
  speed.value = state.mode.speed;
  speedValue.textContent = state.mode.speed;
  speed.addEventListener("input", () => {
    speedValue.textContent = speed.value;
    debouncedPatch({ mode: { speed: Number(speed.value) } });
  });

  const color = document.getElementById("mode-color");
  color.value = rgbToHex(state.mode.color);
  color.addEventListener("input", () => {
    debouncedPatch({ mode: { color: hexToRgb(color.value) } });
  });

  const direction = document.getElementById("mode-direction");
  direction.value = state.mode.direction;
  direction.addEventListener("change", () => {
    postPatch({ mode: { direction: direction.value } });
  });

  const channelToggles = [
    ["mqtt-enabled", "mqtt", "enabled"],
    ["button-enabled", "button", "enabled"],
    ["ir-enabled", "ir", "enabled"],
  ];
  channelToggles.forEach(([id, section, key]) => {
    const el = document.getElementById(id);
    el.checked = state[section][key];
    el.addEventListener("change", () => {
      postPatch({ [section]: { [key]: el.checked } });
    });
  });

  document.getElementById("restart-btn").addEventListener("click", () => {
    if (!confirm("Restart the device now?")) return;
    fetch("/json/restart", { method: "POST" }).then(() => {
      showBanner("Restarting...");
    });
  });
}

function initConfig(state) {
  const form = document.getElementById("config-form");
  const inputs = form.querySelectorAll("[data-key]");

  inputs.forEach((input) => {
    const value = getPath(state, input.dataset.key);
    if (value === undefined) return;
    if (input.type === "checkbox") {
      input.checked = Boolean(value);
    } else if (input.type === "color") {
      input.value = rgbToHex(value);
    } else {
      input.value = value;
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const patch = {};
    inputs.forEach((input) => {
      let value;
      if (input.type === "checkbox") {
        value = input.checked;
      } else if (input.type === "color") {
        value = hexToRgb(input.value);
      } else if (input.type === "number") {
        value = Number(input.value);
      } else {
        value = input.value;
      }
      setPath(patch, input.dataset.key, value);
    });
    postPatch(patch).then(() => showBanner("Saved"));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetchState().then((state) => {
    if (document.getElementById("config-form")) {
      initConfig(state);
    } else if (document.getElementById("mode-current")) {
      initDashboard(state);
    }
  });
});
