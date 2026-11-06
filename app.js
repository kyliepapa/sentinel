/* database.py returns: { ip, mac, role, first_seen, last_seen } */
const state = {
  devices: [],
  scannedAt: null,
  loadError: null,
  filter: "all",
  ascending: true,
  alertsPaused: false,
};
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
function isUnknown(device) {
  return !device.role || device.role.toLowerCase() === "unknown device";
}
function formatDate(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const age = Date.now() - date.getTime();
  if (age < 60000) return "Just now";
  if (age < 3600000) return `${Math.floor(age / 60000)} min ago`;
  if (age < 86400000) return `${Math.floor(age / 3600000)} hr ago`;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
function deviceName(device) {
  return device.role && !isUnknown(device)
    ? device.role.replace(/\b\w/g, (letter) => letter.toUpperCase())
    : "Unknown device";
}
function iconFor(role = "") {
  return (
    { router: "⌁", camera: "▣", laptop: "▱", "unknown device": "?" }[
      role.toLowerCase()
    ] || "◈"
  );
}
function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2800);
}
function renderStats() {
  const unfamiliar = state.devices.filter(isUnknown).length;
  $("#total-devices").textContent = state.devices.length;
  $("#familiar-devices").textContent = state.devices.length - unfamiliar;
  $("#attention-count").textContent = unfamiliar;
  $("#attention-label").textContent =
    `${unfamiliar} device${unfamiliar === 1 ? "" : "s"} to review`;
  $("#nav-device-count").textContent = state.devices.length;
  $("#last-scan").textContent = state.scannedAt ? formatDate(state.scannedAt) : "not yet";
  $("#network-status-title").textContent = unfamiliar ? `${unfamiliar} device${unfamiliar === 1 ? "" : "s"} worth a look` : "Your network is looking healthy";
  $("#network-status-copy").textContent = unfamiliar ? "A quick review will help keep things cozy" : "Everything saved in your Sentinel database looks familiar";
  $("#page-subtitle").textContent = state.loadError ? "Start Sentinel locally to connect this view to your saved scan." : "Here’s the latest picture of what’s connected at home.";
}
function visibleDevices() {
  const filtered =
    state.filter === "all"
      ? state.devices
      : state.devices.filter((device) =>
          state.filter === "unknown" ? isUnknown(device) : !isUnknown(device),
        );
  return [...filtered].sort((a, b) =>
    state.ascending
      ? a.ip.localeCompare(b.ip, undefined, { numeric: true })
      : b.ip.localeCompare(a.ip, undefined, { numeric: true }),
  );
}
function renderDevices() {
  const list = $("#device-list");
  const devices = visibleDevices();
  if (state.loadError) {
    list.innerHTML = `<div class="empty-state"><span class="empty-icon">☁</span><strong>Couldn’t reach the saved scan</strong><p>${state.loadError}</p></div>`;
    $("#view-all").textContent = "Try again →";
    return;
  }
  list.innerHTML = devices.length
    ? devices
        .map(
          (device) =>
            `<article class="device-row"><div class="device-main"><span class="device-avatar ${isUnknown(device) ? "unknown" : ""}">${iconFor(device.role)}</span><div class="device-copy"><strong>${deviceName(device)}</strong><small>${device.ip} · ${device.mac || "MAC unavailable"}</small></div></div><span class="device-role">${device.role || "unknown device"}</span><span class="device-status ${isUnknown(device) ? "unknown" : ""}" title="Last seen ${formatDate(device.last_seen)}"></span></article>`,
        )
        .join("")
    : `<div class="empty-state"><span class="empty-icon">✦</span><strong>No devices here yet</strong><p>Run a scan on your private network, then refresh this page to see what Sentinel finds.</p></div>`;
  $("#view-all").textContent = `View all devices (${state.devices.length}) →`;
}
function renderAlert() {
  const unknown = state.devices.find(isUnknown);
  if (!unknown) {
    $("#alert-panel").hidden = true;
    return;
  }
  $("#alert-panel").hidden = false;
  $("#alert-device-name").textContent = deviceName(unknown);
  $("#alert-device-meta").textContent =
    `${unknown.ip} · ${formatDate(unknown.last_seen)}`;
}
function openModal(title, content) {
  $("#modal-content").innerHTML =
    `<h2 id="modal-title">${title}</h2>${content}`;
  $("#modal-backdrop").hidden = false;
  $("#modal-close").focus();
}
function closeModal() {
  $("#modal-backdrop").hidden = true;
}
async function loadDevices() {
  state.loadError = null;
  try {
    const response = await fetch(window.SENTINEL_API_URL || "/api/devices", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("API unavailable");
    const payload = await response.json();
    state.devices = Array.isArray(payload) ? payload : payload.devices;
    state.scannedAt = Array.isArray(payload) ? null : payload.scanned_at;
    if (!Array.isArray(state.devices))
      throw new Error("Unexpected API response");
  } catch (error) {
    state.devices = [];
    state.scannedAt = null;
    state.loadError = "Run `py server.py` from the sentinel folder, then try again.";
  }
  renderStats();
  renderDevices();
  renderAlert();
}
function bindEvents() {
  $$(".nav-item").forEach((button) =>
    button.addEventListener("click", () => {
      $$(".nav-item").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      $(".breadcrumb strong").textContent = button.textContent
        .replace(/\d+$/, "")
        .trim();
      showToast(
        `${button.textContent.replace(/\d+$/, "").trim()} view selected`,
      );
    }),
  );
  $("#scan-button").addEventListener("click", async () => {
    const label = $("#scan-label");
    label.textContent = "Scanning…";
    $("#scan-button").disabled = true;
    await new Promise((resolve) => setTimeout(resolve, 700));
    await loadDevices();
    label.textContent = "Scan network";
    $("#scan-button").disabled = false;
    showToast("Saved device data refreshed");
  });
  $("#filter-button").addEventListener("click", () => {
    state.filter =
      state.filter === "all"
        ? "unknown"
        : state.filter === "unknown"
          ? "familiar"
          : "all";
    $("#filter-button").firstChild.textContent =
      `${state.filter[0].toUpperCase()}${state.filter.slice(1)} devices `;
    renderDevices();
  });
  $("#sort-button").addEventListener("click", () => {
    state.ascending = !state.ascending;
    renderDevices();
    showToast(`Devices sorted ${state.ascending ? "ascending" : "descending"}`);
  });
  $("#view-all").addEventListener("click", () => {
    state.filter = "all";
    $("#filter-button").firstChild.textContent = "All devices ";
    renderDevices();
  });
  $("#dismiss-alert").addEventListener("click", () => {
    $("#alert-panel").hidden = true;
    showToast("Alert dismissed for this session");
  });
  $("#review-button").addEventListener("click", () => {
    const device = state.devices.find(isUnknown);
    if (device)
      openModal(
        "Review unfamiliar device",
        `<p><strong>${device.ip}</strong> was last seen ${formatDate(device.last_seen)}.</p><p>If you recognize it, update its role in the scanner configuration. Otherwise, disconnect it from your router and rescan.</p>`,
      );
  });
  $("#instructions-button").addEventListener("click", () =>
    openModal(
      "How to remove an unfamiliar device",
      "<ol><li>Open your router’s admin page or mobile app.</li><li>Find the matching IP or MAC address.</li><li>Block or remove it, then change your Wi-Fi password if needed.</li><li>Run another Sentinel scan.</li></ol>",
    ),
  );
  $("#pause-alerts").addEventListener("click", () => {
    state.alertsPaused = !state.alertsPaused;
    $("#alert-toggle").classList.toggle("on", !state.alertsPaused);
    $("#pause-label").textContent = state.alertsPaused
      ? "Alerts are paused"
      : "Alerts are on";
  });
  $("#secure-guide").addEventListener("click", () =>
    openModal(
      "Secure your router",
      "<ul><li>Install the latest firmware.</li><li>Use WPA2 or WPA3 encryption.</li><li>Disable remote administration.</li><li>Choose a unique Wi-Fi password.</li></ul>",
    ),
  );
  $("#notification-button").addEventListener("click", () =>
    showToast("You’re all caught up"),
  );
  $("#upgrade-button").addEventListener("click", () =>
    showToast("Pro features are coming soon"),
  );
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal-backdrop").addEventListener("click", (event) => {
    if (event.target.id === "modal-backdrop") closeModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeModal();
  });
}
document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadDevices();
  document.body.dataset.ready = "true";
});
