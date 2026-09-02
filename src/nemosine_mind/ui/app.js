const state = {
  config: null,
  currentArtifact: null,
  allCycles: null,
};

const elements = {
  form: document.querySelector("#interaction-form"),
  prompt: document.querySelector("#prompt"),
  characterCount: document.querySelector("#character-count"),
  sendButton: document.querySelector("#send-button"),
  providerName: document.querySelector("#provider-name"),
  modelName: document.querySelector("#model-name"),
  privacyNote: document.querySelector("#privacy-note"),
  systemState: document.querySelector("#system-state"),
  sidebarVersion: document.querySelector("#sidebar-version"),
  versionSummary: document.querySelector("#version-summary"),
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
  sectionNav: document.querySelectorAll(".section-nav"),
  controlNav: document.querySelectorAll(".control-nav"),
  controlDrawer: document.querySelector("#control-drawer"),
  controlBackdrop: document.querySelector("#control-backdrop"),
  controlTitle: document.querySelector("#control-title"),
  controlEyebrow: document.querySelector("#control-eyebrow"),
  controlContent: document.querySelector("#control-content"),
  closeControl: document.querySelector("#close-control"),
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
    : "Iniciar ciclo auditável";
}

async function loadConfig() {
  try {
    const config = await request("/v1/config");
    state.config = config;
    elements.providerName.textContent = config.provider || "—";
    elements.modelName.textContent = config.model || "não configurado";
    elements.sidebarVersion.textContent = `v${config.version || "—"}`;
    elements.versionSummary.textContent = `MiND ${config.version || "—"} · estrutura pronta.`;
    elements.systemState.textContent = "Rastreamento ativo";
    elements.privacyNote.textContent =
      config.provider === "mock"
        ? "Modo offline: nenhum dado sai desta máquina."
        : `Armazenamento local; conteúdo enviado a ${config.provider}.`;
  } catch (error) {
    elements.providerName.textContent = "indisponível";
    elements.modelName.textContent = "—";
    elements.systemState.textContent = "Verificação necessária";
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

function providerOption(name, description) {
  const active = state.config?.provider === name.toLowerCase();
  return `
    <article class="control-option ${active ? "active" : ""}">
      <span class="option-symbol" aria-hidden="true">${name.slice(0, 1)}</span>
      <div>
        <div class="option-heading">
          <h3>${escapeHtml(name)}</h3>
          <span class="option-status ${active ? "active" : "planned"}">${active ? "ativo" : "a configurar"}</span>
        </div>
        <p>${escapeHtml(description)}</p>
      </div>
    </article>`;
}

function integrationOption(name, description, status = "não conectado") {
  return `
    <article class="control-option integration-option">
      <span class="option-symbol plug-symbol" aria-hidden="true"></span>
      <div>
        <div class="option-heading">
          <h3>${escapeHtml(name)}</h3>
          <span class="option-status planned">${escapeHtml(status)}</span>
        </div>
        <p>${escapeHtml(description)}</p>
      </div>
    </article>`;
}

async function loadAllCycles() {
  if (state.allCycles) return state.allCycles;
  const cycles = [];
  let offset = 0;
  while (true) {
    const payload = await request(`/v1/cycles?limit=200&offset=${offset}`);
    cycles.push(...payload.cycles);
    if (payload.cycles.length < 200) break;
    offset += payload.cycles.length;
  }
  state.allCycles = cycles;
  return cycles;
}

function storageSummary(cycles) {
  const bytes = new TextEncoder().encode(JSON.stringify(cycles)).length;
  const size = bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${cycles.length.toLocaleString("pt-BR")} ciclos · aproximadamente ${size}`;
}

function downloadJson(records, prefix = "mind-export") {
  const payload = {
    schema: "mind.export/1",
    exported_at: new Date().toISOString(),
    record_count: records.length,
    cycles: records,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${prefix}-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

function filterExport(records, period, subject) {
  const now = new Date();
  const lowerSubject = subject.trim().toLocaleLowerCase("pt-BR");
  return records.filter((cycle) => {
    const created = new Date(cycle.created_at);
    let periodMatch = true;
    if (period === "today") periodMatch = created.toDateString() === now.toDateString();
    if (period === "month") periodMatch = created >= new Date(now.getTime() - 30 * 86400000);
    const text = `${cycle.input?.text || ""} ${cycle.output?.text || ""}`.toLocaleLowerCase("pt-BR");
    return periodMatch && (!lowerSubject || text.includes(lowerSubject));
  });
}

function renderControlPanel(panelName) {
  const version = escapeHtml(state.config?.version || "—");
  if (panelName === "llm") {
    elements.controlEyebrow.textContent = "PROVIDERS E MODELOS";
    elements.controlTitle.textContent = "Seletor de LLM";
    elements.controlContent.innerHTML = `
      <section class="control-intro">
        <span class="control-kicker">ROTEAMENTO CONTROLADO</span>
        <h3>Escolha quem processará a interação</h3>
        <p>O provider ativo continua sendo definido com segurança pela instalação. A seleção persistente e a gestão de chaves serão conectadas nesta frente.</p>
      </section>
      <div class="control-option-list">
        ${providerOption("Mock", "Simulador determinístico, gratuito e totalmente offline.")}
        ${providerOption("OpenAI", "Modelos OpenAI por chave configurada localmente.")}
        ${providerOption("Anthropic", "Modelos Claude por chave configurada localmente.")}
      </div>
      <p class="control-notice">Chaves de API nunca serão incluídas no Cycle Artifact nem exibidas no histórico.</p>`;
    return;
  }

  if (panelName === "integrations") {
    elements.controlEyebrow.textContent = "ECOSSISTEMA MIND";
    elements.controlTitle.textContent = "Plug and Play";
    elements.controlContent.innerHTML = `
      <section class="control-intro">
        <span class="control-kicker">CONEXÕES LOCAIS</span>
        <h3>Integre outros softwares ao middleware</h3>
        <p>Este painel reunirá conectores instaláveis e mostrará quais sistemas estão enviando interações auditáveis ao MiND.</p>
      </section>
      <div class="control-option-list">
        ${integrationOption("Nemosine", "Rastreamento de interações cognitivas e eventos do núcleo.")}
        ${integrationOption("MCL", "Auditoria das interações de IA dentro do aplicativo logístico.")}
        ${integrationOption("Protocolo genérico", "Contrato HTTP/Python para outros softwares compatíveis.", "planejado")}
      </div>`;
    return;
  }

  if (panelName === "export") {
    elements.controlEyebrow.textContent = "PORTABILIDADE DOS REGISTROS";
    elements.controlTitle.textContent = "Exportar dados";
    elements.controlContent.innerHTML = `
      <section class="control-intro">
        <span class="control-kicker">RELATÓRIO AUDITÁVEL</span>
        <h3>Defina o recorte da sessão</h3>
        <p>O arquivo é preparado localmente a partir dos Cycle Artifacts retidos nesta instalação.</p>
      </section>
      <form class="control-form" id="export-form">
        <label>Período
          <select name="period">
            <option value="all">Todo o histórico</option>
            <option value="today">Somente hoje</option>
            <option value="month">Últimos 30 dias</option>
          </select>
        </label>
        <label>Assunto ou termo
          <input name="subject" type="search" placeholder="Ex.: licitação, carreira, contrato" />
        </label>
        <label>Formato
          <select name="format" disabled><option>JSON auditável</option></select>
        </label>
        <button class="primary-button" type="submit">Gerar exportação</button>
        <p class="form-feedback" id="export-feedback" aria-live="polite"></p>
      </form>
      <p class="control-notice">Filtros por heurística serão acrescentados quando as classificações passarem a integrar o artefato de ciclo.</p>`;
    return;
  }

  if (panelName === "cleanup") {
    elements.controlEyebrow.textContent = "RETENÇÃO LOCAL";
    elements.controlTitle.textContent = "Limpar dados";
    elements.controlContent.innerHTML = `
      <section class="control-intro storage-intro">
        <span class="control-kicker">OCUPAÇÃO ESTIMADA</span>
        <strong class="installed-version" id="storage-summary">Calculando…</strong>
        <p>O cálculo considera os registros auditáveis acessíveis nesta instalação.</p>
      </section>
      <article class="danger-card">
        <div>
          <h3>Zerar dados persistidos</h3>
          <p>Esta operação será irreversível. Por segurança, ela só será liberada quando houver backup, confirmação escrita e teste do armazenamento ativo.</p>
        </div>
        <button class="danger-button" type="button" disabled>Limpeza protegida</button>
      </article>
      <p class="control-notice">Nenhum dado foi apagado. A capacidade ocupada será atualizada após cada ciclo.</p>`;
    loadAllCycles().then((cycles) => {
      const summary = document.querySelector("#storage-summary");
      if (summary) summary.textContent = storageSummary(cycles);
    }).catch(() => {
      const summary = document.querySelector("#storage-summary");
      if (summary) summary.textContent = "Não foi possível calcular";
    });
    return;
  }

  if (panelName === "backup") {
    elements.controlEyebrow.textContent = "CÓPIA DE SEGURANÇA";
    elements.controlTitle.textContent = "Fazer backup";
    elements.controlContent.innerHTML = `
      <section class="control-intro">
        <span class="control-kicker">PROTEÇÃO DOS DADOS</span>
        <h3>Copie os registros antes de liberar espaço</h3>
        <p>O backup local já pode ser baixado. A conexão com o Google Drive exigirá autorização explícita da conta.</p>
      </section>
      <div class="control-option-list">
        <article class="control-option active">
          <span class="option-symbol" aria-hidden="true">↓</span>
          <div><div class="option-heading"><h3>Arquivo local</h3><span class="option-status active">disponível</span></div><p>Baixa uma cópia completa em JSON auditável.</p></div>
        </article>
        ${integrationOption("Google Drive", "Envio autenticado para uma pasta escolhida pelo usuário.", "conexão futura")}
      </div>
      <button class="primary-button" id="backup-local" type="button">Baixar backup completo</button>
      <p class="form-feedback" id="backup-feedback" aria-live="polite"></p>`;
    return;
  }

  elements.controlEyebrow.textContent = "MANUTENÇÃO DO SISTEMA";
  elements.controlTitle.textContent = "Verificar atualizações";
  elements.controlContent.innerHTML = `
    <section class="control-intro update-intro">
      <span class="control-kicker">VERSÃO INSTALADA</span>
      <strong class="installed-version">MiND ${version}</strong>
      <p>Canal atual: Windows Preview. As atualizações continuam sob confirmação do usuário.</p>
    </section>
    <article class="update-card">
      <div class="update-icon" aria-hidden="true"></div>
      <div>
        <h3>Consultar versões publicadas</h3>
        <p>Abra a página oficial de releases para comparar a versão instalada com a mais recente.</p>
      </div>
      <a class="primary-button update-link" href="https://github.com/edersouzamelo/nemosine-10-MiND/releases" target="_blank" rel="noreferrer">Ver versões</a>
    </article>
    <p class="control-notice">A verificação automática dentro do aplicativo será adicionada sem instalar nada silenciosamente.</p>`;
}

function setActiveNavigation(activeItem) {
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item === activeItem);
  });
  elements.controlNav.forEach((item) => {
    item.setAttribute("aria-expanded", item === activeItem ? "true" : "false");
  });
}

function openControlPanel(panelName, trigger) {
  closeArtifact();
  renderControlPanel(panelName);
  setActiveNavigation(trigger);
  elements.controlDrawer.classList.add("open");
  elements.controlDrawer.setAttribute("aria-hidden", "false");
  elements.controlBackdrop.classList.remove("hidden");
  elements.closeControl.focus();
}

function closeControlPanel() {
  elements.controlDrawer.classList.remove("open");
  elements.controlDrawer.setAttribute("aria-hidden", "true");
  elements.controlBackdrop.classList.add("hidden");
  const currentSection = window.location.hash === "#cycles" ? elements.sectionNav[1] : elements.sectionNav[0];
  setActiveNavigation(currentSection);
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
    state.allCycles = null;
    await loadCycles();
  } catch (error) {
    elements.responseContent.classList.add("hidden");
    elements.responseEmpty.classList.add("hidden");
    elements.responseError.textContent = error.message;
    elements.responseError.classList.remove("hidden");
    setResponseStatus("Falhou", "failed");
    state.allCycles = null;
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
elements.controlNav.forEach((item) => {
  item.addEventListener("click", () => openControlPanel(item.dataset.controlPanel, item));
});
elements.sectionNav.forEach((item) => {
  item.addEventListener("click", () => {
    closeControlPanel();
    setActiveNavigation(item);
  });
});
elements.closeControl.addEventListener("click", closeControlPanel);
elements.controlBackdrop.addEventListener("click", closeControlPanel);
elements.controlContent.addEventListener("submit", async (event) => {
  if (event.target.id !== "export-form") return;
  event.preventDefault();
  const feedback = document.querySelector("#export-feedback");
  feedback.textContent = "Preparando arquivo…";
  try {
    const data = new FormData(event.target);
    const cycles = await loadAllCycles();
    const filtered = filterExport(cycles, data.get("period"), data.get("subject") || "");
    downloadJson(filtered);
    feedback.textContent = `${filtered.length.toLocaleString("pt-BR")} registros exportados.`;
  } catch (error) {
    feedback.textContent = error.message;
  }
});
elements.controlContent.addEventListener("click", async (event) => {
  if (event.target.id !== "backup-local") return;
  const feedback = document.querySelector("#backup-feedback");
  feedback.textContent = "Preparando backup…";
  try {
    const cycles = await loadAllCycles();
    downloadJson(cycles, "mind-backup");
    feedback.textContent = `${cycles.length.toLocaleString("pt-BR")} registros incluídos no backup.`;
  } catch (error) {
    feedback.textContent = error.message;
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeArtifact();
    closeControlPanel();
  }
});

Promise.all([loadConfig(), loadCycles()]);
