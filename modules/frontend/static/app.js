const form = document.querySelector("#acquisition-form");
const correctionForm = document.querySelector("#correction-form");
const message = document.querySelector("#form-message");
const correctionMessage = document.querySelector("#correction-message");
const kindSelect = document.querySelector("#source-kind");
const locatorInput = document.querySelector("#locator");
const fileInput = document.querySelector("#local-file");
const urlGroup = document.querySelector("#url-input-group");
const fileGroup = document.querySelector("#file-input-group");
const operationsFieldset = document.querySelector("#operations-fieldset");

let latestStatus = null;
let selectedKnowledgeSource = null;
let selectedKnowledgePayload = null;
let selectedKnowledgeTab = "units";

const viewTitles = {
  overview: ["Workspace", "Overview"],
  "source-intake": ["Source Intake", "Acquire and inspect sources"],
  knowledge: ["Knowledge Processing", "Prepared knowledge artifacts"],
  corrections: ["Correction layer", "Review and annotate knowledge"],
  history: ["Processing History", "Pipeline runs and current outputs"]
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
}

function setMessage(target, text, kind = "") {
  target.textContent = text;
  target.className = `form-message ${kind}`;
}

function selectedMode() {
  return form.querySelector("input[name='source_mode']:checked").value;
}

function syncInputMode(forceMode = null) {
  const kind = kindSelect.value;
  const localPreferred = ["document", "note", "image"].includes(kind);
  const localRadio = form.querySelector("input[value='local']");
  const urlRadio = form.querySelector("input[value='url']");
  if (kind === "url") {
    localRadio.disabled = true;
    urlRadio.checked = true;
  } else {
    localRadio.disabled = false;
    if (forceMode) form.querySelector(`input[value='${forceMode}']`).checked = true;
    else if (localPreferred) localRadio.checked = true;
  }
  const mode = selectedMode();
  urlGroup.hidden = mode !== "url";
  fileGroup.hidden = mode !== "local";
  operationsFieldset.hidden = mode !== "url" || kind !== "video";
  locatorInput.required = mode === "url";
  fileInput.required = mode === "local";
  if (kind === "image") fileInput.accept = "image/*";
  else if (kind === "document") fileInput.accept = ".pdf,.doc,.docx,.odt,.rtf,.txt,.md";
  else if (kind === "note") fileInput.accept = ".txt,.md,.markdown,.json,.csv";
  else if (kind === "video") fileInput.accept = "video/*";
  else fileInput.accept = "";
  form.querySelector("button[type='submit']").textContent = mode === "local" ? "Add local file" : "Run acquisition";
}

function activateView(view) {
  if (!viewTitles[view]) return;
  document.querySelectorAll(".nav-item[data-view]").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((item) => {
    item.classList.toggle("active", item.id === `view-${view}`);
  });
  document.querySelector("#view-kicker").textContent = viewTitles[view][0];
  document.querySelector("#view-title").textContent = viewTitles[view][1];
  if (view === "corrections") refreshCorrectionList();
}

function renderArtifacts(source) {
  if (!source.artifacts || source.artifacts.length === 0) return '<p class="popover-empty">No artifact records yet.</p>';
  return `<div class="popover-title">Artifacts</div><ul>${source.artifacts.map((artifact) => `
    <li><span class="artifact-state ${escapeHtml(artifact.state)}">${escapeHtml(artifact.state)}</span><span><strong>${escapeHtml(artifact.kind)}</strong><small>${escapeHtml(artifact.relative_path)}</small></span></li>`).join("")}</ul>`;
}

function renderSourceRows(sources) {
  const rows = document.querySelector("#source-rows");
  if (!sources || sources.length === 0) {
    rows.innerHTML = '<tr><td colspan="5" class="empty">No sources registered yet.</td></tr>';
    return;
  }
  rows.innerHTML = sources.map((source) => `
    <tr>
      <td><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(source.source_id)}</small></td>
      <td>${escapeHtml(source.kind)}</td>
      <td><div class="readiness-wrap"><button class="readiness ${escapeHtml(source.readiness)}" type="button" data-source-id="${escapeHtml(source.source_id)}" aria-expanded="false">${escapeHtml(source.readiness)}</button><div class="artifact-popover" data-popover-for="${escapeHtml(source.source_id)}" hidden>${renderArtifacts(source)}</div></div></td>
      <td>${source.available_artifact_count}/${source.artifact_count}</td>
      <td>${new Date(source.inspected_at).toLocaleString()}</td>
    </tr>`).join("");
  rows.querySelectorAll(".readiness").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const popover = rows.querySelector(`[data-popover-for="${button.dataset.sourceId}"]`);
      const wasOpen = !popover.hidden;
      rows.querySelectorAll(".artifact-popover").forEach((item) => { item.hidden = true; });
      rows.querySelectorAll(".readiness").forEach((item) => item.setAttribute("aria-expanded", "false"));
      popover.hidden = wasOpen;
      button.setAttribute("aria-expanded", String(!wasOpen));
    });
  });
}

function renderModuleStatuses(payload) {
  const knowledge = payload.knowledge || {};
  document.querySelector("#module-status-list").innerHTML = `
    <div class="module-row"><span class="status-dot good"></span><strong>Source Intake</strong><span>stable ${escapeHtml(payload.module_version)}</span></div>
    <div class="module-row"><span class="status-dot good"></span><strong>Data Platform</strong><span>catalog connected</span></div>
    <div class="module-row"><span class="status-dot good"></span><strong>Knowledge Processing</strong><span>stable ${escapeHtml(knowledge.module_version || "1.0.0")}</span></div>
    <div class="module-row muted-row"><span class="status-dot planned-dot"></span><strong>Strategy Blueprint</strong><span>planned</span></div>`;
}

function renderKnowledgeStatus(knowledge) {
  const summary = knowledge.summary || {};
  const processing = knowledge.processing || {};
  document.querySelector("#knowledge-sources").textContent = summary.catalog_sources || 0;
  document.querySelector("#knowledge-processed").textContent = summary.processed_sources || 0;
  document.querySelector("#knowledge-corrections").textContent = summary.corrections || 0;
  document.querySelector("#knowledge-progress").textContent = processing.running ? `${processing.completed}/${processing.total}` : "Idle";
  const rows = document.querySelector("#knowledge-source-rows");
  const sources = knowledge.sources || [];
  if (!sources.length) {
    rows.innerHTML = '<tr><td colspan="5" class="empty">No catalog sources yet.</td></tr>';
  } else {
    rows.innerHTML = sources.map((source) => `
      <tr class="knowledge-source-row" data-source-id="${escapeHtml(source.source_id)}">
        <td><button class="table-link" type="button" data-open-knowledge="${escapeHtml(source.source_id)}"><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(source.source_id)}</small></button></td>
        <td><span class="readiness-text ${escapeHtml(source.readiness)}">${escapeHtml(source.readiness)}</span></td>
        <td><span class="knowledge-state ${source.knowledge_available ? "available" : "missing"}">${source.knowledge_available ? "available" : "not processed"}</span></td>
        <td>${source.chunks_count ?? "-"} / ${source.units_count ?? "-"}</td>
        <td>${source.correction_count || 0}</td>
      </tr>`).join("");
    rows.querySelectorAll("[data-open-knowledge]").forEach((button) => button.addEventListener("click", () => loadKnowledge(button.dataset.openKnowledge)));
    rows.querySelectorAll(".knowledge-source-row").forEach((row) => row.addEventListener("click", (event) => {
      if (event.target.closest("[data-open-knowledge]")) return;
      loadKnowledge(row.dataset.sourceId);
    }));
    if (!selectedKnowledgeSource) {
      const firstProcessed = sources.find((source) => source.knowledge_available);
      if (firstProcessed) loadKnowledge(firstProcessed.source_id);
    }
  }
  renderHistory(sources);
  populateCorrectionSources(sources);
}

function renderHistory(sources) {
  const rows = document.querySelector("#history-rows");
  const processed = (sources || []).filter((source) => source.knowledge_available);
  if (!processed.length) {
    rows.innerHTML = '<tr><td colspan="6" class="empty">No processing history yet.</td></tr>';
    return;
  }
  rows.innerHTML = processed.map((source) => `<tr><td><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(source.source_id)}</small></td><td>${escapeHtml(source.readiness)}</td><td>${escapeHtml(source.pipeline_version || "-")}</td><td>${source.chunks_count ?? 0}</td><td>${source.units_count ?? 0}</td><td>${source.correction_count || 0}</td></tr>`).join("");
}

function renderGlobal(payload) {
  latestStatus = payload;
  const knowledge = payload.knowledge || {};
  const processing = payload.processing || {};
  const knowledgeProcessing = payload.knowledge_processing || {};
  const activeProcessing = processing.running || knowledgeProcessing.running;
  document.querySelector("#module-status").textContent = activeProcessing ? "Processing" : "Connected";
  document.querySelector("#connection-dot").className = "status-dot good";
  document.querySelector("#connection-label").textContent = "Connected";
  const readiness = (payload.summary || {}).readiness || {};
  document.querySelector("#overview-sources").textContent = (payload.summary || {}).source_count || 0;
  document.querySelector("#overview-processed").textContent = (knowledge.summary || {}).processed_sources || 0;
  document.querySelector("#overview-corrections").textContent = (knowledge.summary || {}).corrections || 0;
  document.querySelector("#overview-ready").textContent = readiness.ready || 0;
  renderModuleStatuses(payload);
  renderSourceRows(payload.sources || []);
  renderKnowledgeStatus(knowledge);
  const processButton = document.querySelector("#process-all");
  processButton.disabled = Boolean(processing.running);
  processButton.textContent = processing.running ? `Acquiring ${processing.completed}/${processing.total}` : "Process pending";
  const knowledgeButton = document.querySelector("#process-knowledge");
  knowledgeButton.disabled = Boolean(knowledgeProcessing.running);
  knowledgeButton.textContent = knowledgeProcessing.running ? `Processing ${knowledgeProcessing.completed}/${knowledgeProcessing.total}` : "Process ready sources";
}

function populateCorrectionSources(sources) {
  const select = document.querySelector("#correction-source");
  const previous = selectedKnowledgeSource || select.value;
  select.innerHTML = '<option value="">Select source</option>' + (sources || []).filter((source) => source.knowledge_available).map((source) => `<option value="${escapeHtml(source.source_id)}">${escapeHtml(source.title)} (${escapeHtml(source.source_id)})</option>`).join("");
  if (previous && [...select.options].some((option) => option.value === previous)) select.value = previous;
}

function renderKnowledgeDetail(payload) {
  const artifact = payload.artifact || {};
  const timeline = artifact.timeline || {};
  const corrections = payload.corrections || [];
  const detail = document.querySelector("#knowledge-detail");
  detail.innerHTML = `<div class="detail-heading"><div><p class="eyebrow">${escapeHtml(payload.source_id)}</p><h2>${escapeHtml(timeline.title || payload.source_id)}</h2><p class="muted">Pipeline ${escapeHtml(artifact.pipeline_version || "-")} · ${artifact.chunks?.length || 0} chunks · ${artifact.knowledge_units?.length || 0} units</p></div><button class="secondary" type="button" id="detail-correct">Add correction</button></div>
    <div class="detail-tabs"><button class="detail-tab ${selectedKnowledgeTab === "units" ? "active" : ""}" data-detail-tab="units">Knowledge Units</button><button class="detail-tab ${selectedKnowledgeTab === "chunks" ? "active" : ""}" data-detail-tab="chunks">Chunks</button><button class="detail-tab ${selectedKnowledgeTab === "timeline" ? "active" : ""}" data-detail-tab="timeline">Timeline</button><button class="detail-tab ${selectedKnowledgeTab === "corrections" ? "active" : ""}" data-detail-tab="corrections">Corrections (${corrections.length})</button></div><div id="detail-content"></div>`;
  detail.querySelectorAll("[data-detail-tab]").forEach((button) => button.addEventListener("click", () => { selectedKnowledgeTab = button.dataset.detailTab; renderKnowledgeDetail(payload); }));
  detail.querySelector("#detail-correct").addEventListener("click", () => { document.querySelector("#correction-source").value = payload.source_id; activateView("corrections"); });
  const content = detail.querySelector("#detail-content");
  if (selectedKnowledgeTab === "units") content.innerHTML = renderUnits(artifact.knowledge_units || []);
  if (selectedKnowledgeTab === "chunks") content.innerHTML = renderChunks(artifact.chunks || []);
  if (selectedKnowledgeTab === "timeline") content.innerHTML = renderTimeline(timeline.segments || []);
  if (selectedKnowledgeTab === "corrections") content.innerHTML = renderCorrections(corrections);
  content.querySelectorAll("[data-correction-target]").forEach((button) => button.addEventListener("click", () => {
    document.querySelector("#correction-source").value = payload.source_id;
    document.querySelector("#correction-form [name='target_id']").value = button.dataset.correctionTarget;
    activateView("corrections");
  }));
}

function renderUnits(units) {
  if (!units.length) return '<p class="empty">No knowledge units extracted.</p>';
  return `<div class="detail-list">${units.map((unit) => `<article class="knowledge-card"><div class="knowledge-card-head"><span class="score-pill">${escapeHtml(unit.relevance || "unscored")} · ${escapeHtml(unit.knowledge_score ?? "-")}</span><button class="text-button" type="button" data-correction-target="${escapeHtml(unit.unit_id)}">Correct</button></div><p>${escapeHtml(unit.text)}</p><div class="tag-row">${(unit.concepts || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}${(unit.setup_stages || []).map((tag) => `<span class="tag muted-tag">${escapeHtml(tag)}</span>`).join("")}</div><small>Source chunk: ${escapeHtml(unit.source_chunk_id)}</small></article>`).join("")}</div>`;
}

function renderChunks(chunks) {
  if (!chunks.length) return '<p class="empty">No semantic chunks available.</p>';
  return `<div class="detail-list">${chunks.map((chunk) => `<article class="knowledge-card"><div class="knowledge-card-head"><strong>${escapeHtml(chunk.chunk_id)}</strong><button class="text-button" type="button" data-correction-target="${escapeHtml(chunk.chunk_id)}">Correct</button></div><p>${escapeHtml(chunk.semantic?.summary || chunk.combined_transcript || "")}</p><small>${escapeHtml(chunk.start)} - ${escapeHtml(chunk.end)} · ${escapeHtml((chunk.semantic?.topics || []).join(", "))}</small></article>`).join("")}</div>`;
}

function renderTimeline(segments) {
  if (!segments.length) return '<p class="empty">No timeline segments available.</p>';
  return `<div class="detail-list timeline-list">${segments.slice(0, 120).map((segment, index) => `<article class="timeline-row"><span class="timecode">${formatTime(segment.start)}<br>${formatTime(segment.end)}</span><div><p>${escapeHtml(segment.transcript || "")}</p><small>${segment.frame_paths?.length || 0} frames · ${segment.ocr_texts?.length || 0} OCR records · ${segment.events?.length || 0} events</small></div><button class="text-button" type="button" data-correction-target="segment_${index}">Correct</button></article>`).join("")}</div>`;
}

function renderCorrections(corrections) {
  if (!corrections.length) return '<p class="empty">No corrections recorded for this source.</p>';
  return `<div class="detail-list">${corrections.slice().reverse().map((item) => `<article class="correction-card"><div class="knowledge-card-head"><strong>${escapeHtml(item.target_type)} · ${escapeHtml(item.target_id)}</strong><span class="tag">${escapeHtml(item.field)}</span></div><p>${escapeHtml(typeof item.corrected_value === "string" ? item.corrected_value : JSON.stringify(item.corrected_value))}</p><small>${escapeHtml(item.reason)} · ${escapeHtml(item.author)} · ${new Date(item.created_at).toLocaleString()}</small></article>`).join("")}</div>`;
}

function formatTime(value) {
  const seconds = Math.max(0, Number(value) || 0);
  return `${Math.floor(seconds / 60).toString().padStart(2, "0")}:${Math.floor(seconds % 60).toString().padStart(2, "0")}`;
}

async function loadKnowledge(sourceId) {
  try {
    const response = await fetch(`/api/knowledge/${encodeURIComponent(sourceId)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Could not load knowledge artifact");
    selectedKnowledgeSource = sourceId;
    selectedKnowledgePayload = payload;
    selectedKnowledgeTab = "units";
    renderKnowledgeDetail(payload);
    activateView("knowledge");
    document.querySelector("#correction-source").value = sourceId;
  } catch (error) {
    setMessage(message, error.message, "error");
  }
}

async function refreshCorrectionList() {
  const sourceId = document.querySelector("#correction-source").value;
  const list = document.querySelector("#correction-list");
  if (!sourceId) { list.innerHTML = '<p class="empty">Select a source to view corrections.</p>'; return; }
  try {
    const response = await fetch(`/api/knowledge/${encodeURIComponent(sourceId)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Could not load corrections");
    list.innerHTML = renderCorrections(payload.corrections || []);
  } catch (error) {
    list.innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`;
  }
}

async function refreshStatus() {
  const response = await fetch("/api/status");
  if (!response.ok) throw new Error("Could not load status");
  renderGlobal(await response.json());
  if (selectedKnowledgeSource && selectedKnowledgePayload) {
    const refreshed = await fetch(`/api/knowledge/${encodeURIComponent(selectedKnowledgeSource)}`);
    if (refreshed.ok) { selectedKnowledgePayload = await refreshed.json(); renderKnowledgeDetail(selectedKnowledgePayload); }
  }
}

kindSelect.addEventListener("change", () => syncInputMode());
form.querySelectorAll("input[name='source_mode']").forEach((input) => input.addEventListener("change", () => syncInputMode()));
syncInputMode("url");

document.querySelectorAll(".nav-item[data-view]").forEach((item) => item.addEventListener("click", () => activateView(item.dataset.view)));
document.querySelectorAll("[data-go-view]").forEach((item) => item.addEventListener("click", () => activateView(item.dataset.goView)));
document.querySelector("#correction-source").addEventListener("change", refreshCorrectionList);
document.querySelector("#refresh").addEventListener("click", () => refreshStatus().catch((error) => setMessage(message, error.message, "error")));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const mode = selectedMode();
  if (mode === "local") {
    data.delete("source_mode"); data.delete("locator"); data.delete("download_video"); data.delete("fetch_metadata"); data.delete("fetch_subtitles");
    setMessage(message, "Adding local file...");
    try {
      const response = await fetch("/api/source-intake/upload", {method: "POST", body: data});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Upload failed");
      renderGlobal(result.status); setMessage(message, `Added. Stored artifacts: ${result.stored_artifact_count}.`, "success");
    } catch (error) { setMessage(message, error.message, "error"); }
    return;
  }
  const payload = {source_id: data.get("source_id"), locator: data.get("locator"), title: data.get("title"), kind: data.get("kind"), download_video: data.has("download_video"), fetch_metadata: data.has("fetch_metadata"), fetch_subtitles: data.has("fetch_subtitles")};
  setMessage(message, "Running acquisition...");
  try {
    const response = await fetch("/api/source-intake/acquire", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Acquisition failed");
    renderGlobal(result.status); setMessage(message, `Completed. Stored artifacts: ${result.stored_artifact_count}.`, "success");
  } catch (error) { setMessage(message, error.message, "error"); }
});

document.querySelector("#process-all").addEventListener("click", async () => {
  setMessage(message, "Starting source processing...");
  try {
    const response = await fetch("/api/source-intake/process-all", {method: "POST"});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not start processing");
    setMessage(message, result.message || "Source processing started.");
  } catch (error) { setMessage(message, error.message, "error"); }
});

document.querySelector("#process-knowledge").addEventListener("click", async () => {
  try {
    const response = await fetch("/api/knowledge/process", {method: "POST", headers: {"Content-Type": "application/json"}, body: "{}"});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not start knowledge processing");
  } catch (error) { setMessage(message, error.message, "error"); }
});

correctionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const sourceId = document.querySelector("#correction-source").value;
  if (!sourceId) { setMessage(correctionMessage, "Select a source first.", "error"); return; }
  const data = new FormData(correctionForm);
  let correctedValue = data.get("corrected_value");
  try { if (/^(\[|\{|true$|false$|-?\d+(\.\d+)?$)/.test(correctedValue.trim())) correctedValue = JSON.parse(correctedValue); } catch (_) { /* keep operator text */ }
  const payload = {target_type: data.get("target_type"), target_id: data.get("target_id"), field: data.get("field"), corrected_value: correctedValue, reason: data.get("reason"), author: data.get("author")};
  try {
    const response = await fetch(`/api/knowledge/${encodeURIComponent(sourceId)}/corrections`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not save correction");
    setMessage(correctionMessage, "Correction appended.", "success");
    correctionForm.querySelector("[name='corrected_value']").value = "";
    correctionForm.querySelector("[name='reason']").value = "";
    refreshCorrectionList();
    if (selectedKnowledgeSource === sourceId) { selectedKnowledgePayload = result.knowledge; renderKnowledgeDetail(selectedKnowledgePayload); }
    refreshStatus().catch(() => {});
  } catch (error) { setMessage(correctionMessage, error.message, "error"); }
});

document.addEventListener("click", () => {
  document.querySelectorAll(".artifact-popover").forEach((item) => { item.hidden = true; });
  document.querySelectorAll(".readiness").forEach((item) => item.setAttribute("aria-expanded", "false"));
});

refreshStatus().catch((error) => {
  document.querySelector("#connection-dot").className = "status-dot bad";
  document.querySelector("#connection-label").textContent = "Offline";
  setMessage(message, error.message, "error");
});
setInterval(() => refreshStatus().catch(() => {}), 4000);
