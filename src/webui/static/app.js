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

function initNav() {
  const toggle = document.getElementById("menu-toggle");
  const nav = document.getElementById("main-nav");
  if (!toggle || !nav) return;
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
}

function initDashboard(state) {
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

function updateCollapsible(checkbox) {
  const targetId = checkbox.dataset.toggles;
  if (!targetId) return;
  const target = document.getElementById(targetId);
  if (target) target.hidden = !checkbox.checked;
}

function initFormPage(formId, state) {
  const form = document.getElementById(formId);
  if (!form) return;
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
    if (input.dataset.toggles) {
      updateCollapsible(input);
      input.addEventListener("change", () => updateCollapsible(input));
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

function initLedTest() {
  const button = document.getElementById("leds-test-btn");
  const countInput = document.getElementById("leds-count-input");
  if (!button || !countInput) return;
  button.addEventListener("click", () => {
    const count = Number(countInput.value);
    if (!count || count < 1) return;
    postPatch({
      leds: { count },
      mode: { on: true, current: "blink" },
    }).then(() => showBanner("Blinking " + count + " LEDs"));
  });
}

function renderScanResults(results) {
  const list = document.getElementById("wifi-scan-results");
  if (!list) return;
  list.innerHTML = "";
  if (!results.length) {
    const li = document.createElement("li");
    li.textContent = "No networks found";
    list.appendChild(li);
    return;
  }
  results
    .slice()
    .sort((a, b) => b.rssi - a.rssi)
    .forEach((net) => {
      const li = document.createElement("li");
      const name = document.createElement("span");
      name.textContent = net.ssid + (net.open ? "" : " (secured)");
      const signal = document.createElement("span");
      signal.className = "signal";
      signal.textContent = net.rssi + " dBm";
      li.appendChild(name);
      li.appendChild(signal);
      li.addEventListener("click", () => {
        const ssidField = document.querySelector('[data-key="wifi.ssid"]');
        if (ssidField) ssidField.value = net.ssid;
      });
      list.appendChild(li);
    });
}

function initWifiScan() {
  const button = document.getElementById("wifi-scan-btn");
  if (!button) return;
  button.addEventListener("click", () => {
    button.disabled = true;
    button.textContent = "Scanning...";
    fetch("/json/wifi/scan", { method: "POST" }).then(() => {
      let attempts = 0;
      const poll = () => {
        attempts += 1;
        fetchState().then((state) => {
          const wifi = state.runtime && state.runtime.wifi ? state.runtime.wifi : {};
          if (!wifi.scan_requested || attempts >= 10) {
            button.disabled = false;
            button.textContent = "Scan for networks";
            renderScanResults(wifi.scan_results || []);
          } else {
            setTimeout(poll, 700);
          }
        });
      };
      setTimeout(poll, 700);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initNav();
  fetchState().then((state) => {
    if (document.getElementById("mode-current")) {
      initDashboard(state);
    }
    initFormPage("config-form", state);
    initFormPage("modes-form", state);
    initLedTest();
    initWifiScan();
  });
});
