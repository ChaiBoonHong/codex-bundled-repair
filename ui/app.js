const buttons = [...document.querySelectorAll("[data-action]")];
const activityLog = document.getElementById("activity-log");
const connectionMessage = document.getElementById("connection-message");
const connectionDot = document.getElementById("connection-dot");
const overallState = document.getElementById("overall-state");
const activityState = document.getElementById("activity-state");
let busy = false;

function setBusy(value) {
  busy = value;
  buttons.forEach((button) => {
    button.disabled = value || !window.pywebview?.api;
    button.setAttribute("aria-busy", String(value));
  });
  activityState.innerHTML = value
    ? '<span class="size-1.5 animate-pulse rounded-full bg-blue-500 motion-reduce:animate-none" aria-hidden="true"></span>Working'
    : '<span class="size-1.5 rounded-full bg-slate-300" aria-hidden="true"></span>Ready';
}

function addLog(message, tone = "normal") {
  const line = document.createElement("p");
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  line.className = tone === "error" ? "text-rose-700" : tone === "success" ? "text-emerald-700" : "text-slate-600";
  line.textContent = `${time}  ${message}`;
  activityLog.append(line);
  activityLog.scrollTop = activityLog.scrollHeight;
}

function setOverall(text, tone) {
  overallState.textContent = text;
  overallState.className = tone === "good"
    ? "rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-semibold text-emerald-800"
    : tone === "attention"
      ? "rounded-full bg-amber-100 px-3 py-1.5 text-xs font-semibold text-amber-900"
      : "rounded-full bg-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600";
}

function renderPlugin(name, status) {
  const displayName = name === "chrome" ? "Chrome" : "Computer Use";
  const prefix = name === "chrome" ? "chrome" : "computer-use";
  const ready = status.installed && status.enabled && status.cache_ok;
  const badge = document.getElementById(`${prefix}-badge`);
  badge.textContent = ready ? "Ready" : "Needs attention";
  badge.className = ready
    ? "rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800"
    : "rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-900";
  document.getElementById(`${prefix}-detail`).textContent = ready
    ? `${displayName} is installed, enabled, and its cache matches the bundled source.`
    : `${displayName} may need repair. Review the check details before choosing Repair.`;
  document.getElementById(`${prefix}-installed`).textContent = status.installed ? "Yes" : "No";
  document.getElementById(`${prefix}-enabled`).textContent = status.enabled ? "Yes" : "No";
  document.getElementById(`${prefix}-cache`).textContent = status.cache_ok ? "Valid" : "Check";
  return ready;
}

function renderStatus(statuses) {
  const ready = Object.entries(statuses).map(([name, status]) => renderPlugin(name, status)).every(Boolean);
  setOverall(ready ? "All checked" : "Needs attention", ready ? "good" : "attention");
}

function renderEvent(event) {
  if (event.type === "log") addLog(event.message);
  if (event.type === "error") {
    addLog(event.message, "error");
    setOverall("Check stopped", "attention");
  }
  if (event.type === "status") renderStatus(event.statuses);
  if (event.type === "complete") {
    if (event.code === 0) {
      addLog("Action completed.", "success");
      if (event.action !== "inspect") setOverall("Complete", "good");
    } else if (event.code === 2) {
      addLog("No further changes were made.");
      setOverall("Review result", "attention");
    } else {
      setOverall("Check stopped", "attention");
    }
  }
}

async function pollEvents() {
  try {
    const result = await window.pywebview.api.poll();
    result.events.forEach(renderEvent);
    if (result.running) {
      window.setTimeout(pollEvents, 250);
    } else {
      setBusy(false);
    }
  } catch (error) {
    addLog(`The desktop bridge stopped responding: ${error.message}`, "error");
    setBusy(false);
  }
}

async function runAction(action) {
  if (busy || !window.pywebview?.api) return;
  setBusy(true);
  addLog(`${action === "test" ? "Starting guided test" : `${action[0].toUpperCase()}${action.slice(1)} in progress`}…`);
  try {
    const result = await window.pywebview.api.start(action);
    if (!result.started) {
      addLog(result.message || "Another action is already running.");
      setBusy(false);
      return;
    }
    pollEvents();
  } catch (error) {
    addLog(error.message || "The action could not be started.", "error");
    setBusy(false);
  }
}

buttons.forEach((button) => button.addEventListener("click", () => runAction(button.dataset.action)));

function connect() {
  connectionMessage.textContent = "Connected to the local repair engine";
  connectionDot.className = "size-2 rounded-full bg-emerald-400";
  setBusy(false);
  runAction("inspect");
}

if (window.pywebview?.api) connect();
else window.addEventListener("pywebviewready", connect, { once: true });
