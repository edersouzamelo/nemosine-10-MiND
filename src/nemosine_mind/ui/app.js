const state = {
  config: null,
  currentArtifact: null,
};

const elements = {
  form: document.querySelector("#interaction-form"),
  prompt: document.querySelector("#prompt"),
  characterCount: document.querySelector("#character-count"),
  sendButton: document.querySelector("#send-button"),
  providerName: document.querySelector("#provider-name"),
  modelName: document.querySelector("#model-name"),
  privacyNote: document.querySelector("#privacy-note"),
  responseStatus: document.querySelector("#response-status"),
  responseEmpty: document.querySelector("#response-empty"),
  responseContent: document.querySelector("#response-content"),
  responseText: document.querySelector("#response-text"),
  responseError: document.querySelector("#response-error"),
  cycleId: document.querySelector("#cycle-id"),
  cycleLatency: document.querySelector("#cycle-latency"),
  cycleTime: document.querySelector("#cycle-time"),
  inspectLatest: document.querySelector("#inspect-latest"),
  historyList: document.querySelector("#history-list"),
  refreshCycles: document.querySelector("#refresh-cycles"),
  drawer: document.querySelector("#artifact-drawer"),
  drawerBackdrop: document.querySelector("#drawer-backdrop"),
  drawerContent: document.querySelector("#artifact-content"),
  closeDrawer: document.querySelector("#close-drawer"),
};

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw new Error(payload?.detail || `Falha HTTP ${response.status}`);
  }
  return payload;
}

function formatDate(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(parsed);
}

function setResponseStatus(label, statusClass) {
  elements.responseStatus.textContent = label;
  elements.responseStatus.className = `status-chip ${statusClass}`;
}

function setLoading(isLoading) {
  elements.sendButton.disabled = isLoading;
  elements.prompt.disabled = isLoading;
  elements.sendButton.querySelector("span").textContent = isLoading
    ? "Executando…"
    : "Executar ciclo";
}

async function loadConfig() {
  try {
    const config = await request("/v1/config");
    state.config = config;
    elements.providerName.textContent = config.provider || "—";
    elements.modelName.textContent = config.model || "não configurado";
    elements.privacyNote.textContent =
      config.provider === "mock"
        ? "Modo offline: nenhum dado sai desta máquina."
        : `Armazenamento local; conteúdo enviado a ${config.provider}.`;
  } catch (error) {
    elements.providerName.textContent = "indisponível";
    elements.modelName.textContent = "—";
    elements.privacyNote.textContent = error.message;
  }
}

function historyItem(cycle) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "history-item";
  button.dataset.cycleId = cycle.cycle_id;

  const top = document.createElement("div");
  top.className = "history-item-top";
  const id = document.createElement("strong");
  id.textContent = cycle.cycle_id;
  const status = document.createElement("span");
  status.className = `history-item-status ${cycle.status === "failed" ? "failed" : ""}`;
  status.textContent = cycle.status === "failed" ? "falhou" : "concluído";
  top.append(id, status);

  const preview = document.createElement("p");
  preview.className = "history-item-preview";
  preview.textContent = cycle.input?.text || "Interação sem texto registrado";

  const meta = document.createElement("div");
  meta.className = "history-item-meta";
  const provider = document.createElement("span");
  provider.textContent = `${cycle.provider?.name || "—"} / ${cycle.provider?.model || "—"}`;
  const date = document.createElement("time");
  date.textContent = formatDate(cycle.created_at);
  meta.append(provider, date);

  button.append(top, preview, meta);
  button.addEventListener("click", () => openArtifact(cycle.cycle_id));
  return button;
}

async function loadCycles() {
  elements.historyList.innerHTML = '<div class="history-loading">Carregando ciclos…</div>';
  try {
    const payload = await request("/v1/cycles?limit=20&offset=0");
    elements.historyList.replaceChildren();
    if (!payload.cycles.length) {
      elements.historyList.innerHTML =
        '<div class="history-empty">Nenhum ciclo registrado ainda.</div>';
      return;
    }
    payload.cycles.forEach((cycle) => elements.historyList.append(historyItem(cycle)));
  } catch (error) {
    elements.historyList.innerHTML = `<div class="error-message">${escapeHtml(error.message)}</div>`;
  }
}

function escapeHtml(value) {
  const node = document.createElement("div");
  node.textContent = String(value ?? "");
  return node.innerHTML;
}

function artifactSection(title, value, textOnly = false) {
  const content = textOnly ? String(value || "—") : JSON.stringify(value ?? {}, null, 2);
  return `
    <section class="artifact-section">
      <h3>${escapeHtml(title)}</h3>
      ${textOnly ? `<p class="artifact-text">${escapeHtml(content)}</p>` : `<pre>${escapeHtml(content)}</pre>`}
    </section>`;
}

function renderArtifact(artifact) {
  const provider = `${artifact.provider?.name || "—"} / ${artifact.provider?.model || "—"}`;
  const errorSection = artifact.error
    ? artifactSection("Erro", artifact.error)
    : "";
  elements.drawerContent.innerHTML = `
    <section class="artifact-overview">
      <dl class="artifact-grid">
        <div><dt>Cycle ID</dt><dd>${escapeHtml(artifact.cycle_id)}</dd></div>
        <div><dt>Status</dt><dd>${escapeHtml(artifact.status)}</dd></div>
        <div><dt>Provider / modelo</dt><dd>${escapeHtml(provider)}</dd></div>
        <div><dt>Latência</dt><dd>${escapeHtml(artifact.duration_ms)} ms</dd></div>
        <div><dt>Início</dt><dd>${escapeHtml(formatDate(artifact.created_at))}</dd></div>
        <div><dt>Conclusão</dt><dd>${escapeHtml(formatDate(artifact.completed_at))}</dd></div>
        <div><dt>Schema</dt><dd>${escapeHtml(artifact.schema_version)}</dd></div>
        <div><dt>Request ID</dt><dd>${escapeHtml(artifact.provider?.request_id || "—")}</dd></div>
      </dl>
    </section>
    ${artifactSection("Input", artifact.input?.text, true)}
    ${artifactSection("Configuração", artifact.config)}
    ${artifactSection("Provider", artifact.provider)}
    ${artifactSection("Output", artifact.output?.text, true)}
    ${errorSection}
    ${artifactSection("Extensões", artifact.extensions)}
  `;
}

async function openArtifact(cycleOrId) {
  try {
    const artifact =
      typeof cycleOrId === "string"
        ? await request(`/v1/cycles/${encodeURIComponent(cycleOrId)}`)
        : cycleOrId;
    state.currentArtifact = artifact;
    renderArtifact(artifact);
    elements.drawer.classList.add("open");
    elements.drawer.setAttribute("aria-hidden", "false");
    elements.drawerBackdrop.classList.remove("hidden");
    elements.closeDrawer.focus();
  } catch (error) {
    elements.responseError.textContent = error.message;
    elements.responseError.classList.remove("hidden");
  }
}

function closeArtifact() {
  elements.drawer.classList.remove("open");
  elements.drawer.setAttribute("aria-hidden", "true");
  elements.drawerBackdrop.classList.add("hidden");
}

async function runInteraction(event) {
  event.preventDefault();
  const text = elements.prompt.value.trim();
  if (!text) return;

  setLoading(true);
  setResponseStatus("Executando", "running");
  elements.responseError.classList.add("hidden");

  try {
    const payload = await request("/v1/interactions", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    const artifact = payload.artifact;
    state.currentArtifact = artifact;
    elements.responseEmpty.classList.add("hidden");
    elements.responseContent.classList.remove("hidden");
    elements.responseText.textContent = payload.reply;
    elements.cycleId.textContent = payload.cycle_id;
    elements.cycleId.title = "Clique para copiar o cycle_id";
    elements.cycleLatency.textContent = `${artifact.duration_ms} ms`;
    elements.cycleTime.textContent = formatDate(artifact.completed_at);
    setResponseStatus("Concluído", "succeeded");
    await loadCycles();
  } catch (error) {
    elements.responseContent.classList.add("hidden");
    elements.responseEmpty.classList.add("hidden");
    elements.responseError.textContent = error.message;
    elements.responseError.classList.remove("hidden");
    setResponseStatus("Falhou", "failed");
    await loadCycles();
  } finally {
    setLoading(false);
  }
}

elements.prompt.addEventListener("input", () => {
  elements.characterCount.textContent = `${elements.prompt.value.length.toLocaleString("pt-BR")} / 20.000`;
});
elements.form.addEventListener("submit", runInteraction);
elements.refreshCycles.addEventListener("click", loadCycles);
elements.inspectLatest.addEventListener("click", () => {
  if (state.currentArtifact) openArtifact(state.currentArtifact);
});
elements.cycleId.addEventListener("click", async () => {
  if (!state.currentArtifact) return;
  await navigator.clipboard?.writeText(state.currentArtifact.cycle_id);
  elements.cycleId.textContent = "copiado";
  window.setTimeout(() => {
    elements.cycleId.textContent = state.currentArtifact.cycle_id;
  }, 900);
});
elements.closeDrawer.addEventListener("click", closeArtifact);
elements.drawerBackdrop.addEventListener("click", closeArtifact);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeArtifact();
});

Promise.all([loadConfig(), loadCycles()]);
