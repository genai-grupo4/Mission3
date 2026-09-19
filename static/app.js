const bootLines = [
  "INICIALIZANDO NUCLEO J.A.R.V.I.S.",
  "CONECTANDO A OPENROUTER",
  "CARGANDO 4 MODELOS",
  "SISTEMA LISTO",
];

const state = {
  model: null,
  effort: null,
  sessionCost: 0,
  models: [],
  activeLogFile: null,
};

const els = {
  boot: document.getElementById("boot"),
  bootLines: document.getElementById("boot-lines"),
  app: document.getElementById("app"),
  reactor: document.getElementById("reactor"),
  slots: document.getElementById("slots"),
  effortToggle: document.getElementById("effort-toggle"),
  statusPill: document.getElementById("status-pill"),
  historyList: document.getElementById("history-list"),
  chatPanel: document.getElementById("chat-panel"),
  chatEmpty: document.getElementById("chat-empty"),
  inputForm: document.getElementById("input-form"),
  inputText: document.getElementById("input-text"),
  sendBtn: document.getElementById("send-btn"),
  activeModel: document.getElementById("active-model"),
  activeLog: document.getElementById("active-log"),
  sessionCost: document.getElementById("session-cost"),
};

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function playBoot() {
  for (const line of bootLines) {
    const div = document.createElement("div");
    div.className = "line";
    div.textContent = line;
    els.bootLines.appendChild(div);
    await sleep(220);
    div.classList.add("ok");
  }
  await sleep(300);
  els.boot.classList.add("hidden");
  els.app.classList.remove("hidden");
  await sleep(400);
  els.boot.remove();
}

function setStatus(text, kind) {
  els.statusPill.textContent = text;
  els.statusPill.className = "status-pill" + (kind ? " " + kind : "");
}

function setThinking(on) {
  els.reactor.classList.toggle("thinking", on);
}

async function loadModels() {
  const res = await fetch("/api/models");
  const models = await res.json();
  state.models = models;
  els.slots.innerHTML = "";
  models.forEach((m) => {
    const btn = document.createElement("button");
    btn.className = "slot-btn";
    btn.dataset.slot = m.slot;
    btn.innerHTML = `
      <span class="num">SLOT ${m.slot}</span>
      <span class="label">${m.label}</span>
      <span class="cap">${m.capability}</span>
    `;
    btn.addEventListener("click", () => selectSlot(m.slot, btn));
    els.slots.appendChild(btn);
  });
}

function renderEffort(effort, supported) {
  [...els.effortToggle.querySelectorAll("button")].forEach((b) => {
    b.classList.toggle("active", b.dataset.effort === effort);
    b.disabled = supported === false && b.dataset.effort !== "off";
  });
}

function formatTs(ts) {
  const m = ts.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/);
  return m ? `${m[3]}/${m[2]} ${m[4]}:${m[5]}` : ts;
}

function zeroUsage() {
  return { prompt_tokens: 0, completion_tokens: 0, reasoning_tokens: 0, cached_tokens: 0, cost: 0 };
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const bySlot = await res.json();
  els.historyList.innerHTML = "";

  const slots = Object.keys(bySlot).sort();
  if (slots.every((s) => bySlot[s].length === 0)) {
    els.historyList.innerHTML = `<div class="history-empty">SIN CONVERSACIONES PREVIAS</div>`;
    return;
  }

  slots.forEach((slot) => {
    const entries = bySlot[slot];
    if (!entries.length) return;
    const model = state.models.find((m) => m.slot === slot);

    const group = document.createElement("div");
    group.className = "history-group";
    group.innerHTML = `<div class="group-label">${escapeHtml(model ? model.label : "SLOT " + slot)}</div>`;

    entries.forEach((entry) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "history-entry" + (entry.file === state.activeLogFile ? " active" : "");
      btn.innerHTML = `<span class="ts">${formatTs(entry.started_at)}</span><span class="preview">${escapeHtml(entry.preview)}</span>`;
      btn.addEventListener("click", () => loadHistoryEntry(entry.file));
      group.appendChild(btn);
    });

    els.historyList.appendChild(group);
  });
}

async function loadHistoryEntry(file) {
  setStatus("CARGANDO", "busy");
  try {
    const res = await fetch("/api/history/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "error cargando historial");

    [...els.slots.querySelectorAll(".slot-btn")].forEach((b) =>
      b.classList.toggle("active", b.dataset.slot === data.model.slot)
    );

    state.model = data.model;
    state.effort = data.reasoning_effort;
    state.sessionCost = 0;
    state.activeLogFile = file;

    els.activeModel.textContent = data.model.id;
    els.activeLog.textContent = data.log_path;

    renderEffort(state.effort, data.model.supports_effort);

    els.chatPanel.innerHTML = "";
    addSystemMessage(`Conversación cargada — ${data.model.label} (${data.model.id})`);
    data.history.forEach((turn) => {
      if (turn.role === "user") {
        addUserMessage(turn.content);
      } else {
        addAssistantMessage(turn.content, turn.usage || zeroUsage());
      }
    });
    els.sessionCost.textContent = "$" + state.sessionCost.toFixed(6);

    els.inputText.disabled = false;
    els.sendBtn.disabled = false;
    els.inputText.focus();

    setStatus("EN LINEA");
    loadHistory();
  } catch (e) {
    setStatus("ERROR", "error");
    addErrorMessage(e.message);
  }
}

async function selectSlot(slot, btn) {
  setStatus("CONECTANDO", "busy");
  try {
    const res = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "error de sesion");

    [...els.slots.querySelectorAll(".slot-btn")].forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    state.model = data.model;
    state.effort = data.reasoning_effort;
    state.sessionCost = 0;
    state.activeLogFile = data.log_path.split("/").pop();

    els.activeModel.textContent = data.model.id;
    els.activeLog.textContent = data.log_path;
    els.sessionCost.textContent = "$0.000000";

    renderEffort(state.effort, data.model.supports_effort);

    els.chatPanel.innerHTML = "";
    addSystemMessage(`Nueva conversación iniciada — ${data.model.label} (${data.model.id})`);

    els.inputText.disabled = false;
    els.sendBtn.disabled = false;
    els.inputText.focus();

    setStatus("EN LINEA");
    loadHistory();
  } catch (e) {
    setStatus("ERROR", "error");
    addErrorMessage(e.message);
  }
}

async function setEffort(effort) {
  if (!state.model) return;
  try {
    const res = await fetch("/api/reasoning", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ effort }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    state.effort = data.reasoning_effort;
    renderEffort(state.effort, state.model.supports_effort);
  } catch (e) {
    addErrorMessage(e.message);
  }
}

function addSystemMessage(text) {
  els.chatEmpty.remove();
  const div = document.createElement("div");
  div.className = "msg system";
  div.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  els.chatPanel.appendChild(div);
  scrollToBottom();
}

function addErrorMessage(text) {
  const div = document.createElement("div");
  div.className = "msg error";
  div.innerHTML = `<div class="bubble">⚠ ${escapeHtml(text)}</div>`;
  els.chatPanel.appendChild(div);
  scrollToBottom();
}

function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `<div class="role">VOS</div><div class="bubble">${escapeHtml(text)}</div>`;
  els.chatPanel.appendChild(div);
  scrollToBottom();
}

function addAssistantMessage(text, usage) {
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.innerHTML = `
    <div class="role">J.A.R.V.I.S.</div>
    <div class="bubble">${escapeHtml(text)}</div>
    <div class="telemetry">
      <span class="chip">IN <b>${usage.prompt_tokens}</b></span>
      <span class="chip">OUT <b>${usage.completion_tokens}</b></span>
      <span class="chip">THINK <b>${usage.reasoning_tokens}</b></span>
      <span class="chip">CACHED <b>${usage.cached_tokens}</b></span>
      <span class="chip cost">COST <b>$${usage.cost}</b></span>
    </div>
  `;
  els.chatPanel.appendChild(div);
  scrollToBottom();

  state.sessionCost += usage.cost || 0;
  els.sessionCost.textContent = "$" + state.sessionCost.toFixed(6);
}

function scrollToBottom() {
  els.chatPanel.scrollTop = els.chatPanel.scrollHeight;
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

async function sendMessage(text) {
  addUserMessage(text);
  els.inputText.disabled = true;
  els.sendBtn.disabled = true;
  setStatus("PROCESANDO", "busy");
  setThinking(true);

  try {
    const res = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "error");
    addAssistantMessage(data.text, data.usage);
    setStatus("EN LINEA");
    loadHistory();
  } catch (e) {
    addErrorMessage(e.message);
    setStatus("ERROR", "error");
  } finally {
    setThinking(false);
    els.inputText.disabled = false;
    els.sendBtn.disabled = false;
    els.inputText.focus();
  }
}

els.effortToggle.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-effort]");
  if (btn && !btn.disabled) setEffort(btn.dataset.effort);
});

els.inputForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = els.inputText.value.trim();
  if (!text) return;
  els.inputText.value = "";
  sendMessage(text);
});

(async function init() {
  await Promise.all([playBoot(), loadModels()]);
  loadHistory();
})();
