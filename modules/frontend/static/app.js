const form = document.querySelector("#acquisition-form");
const message = document.querySelector("#form-message");
const kindSelect = document.querySelector("#source-kind");
const locatorInput = document.querySelector("#locator");
const fileInput = document.querySelector("#local-file");
const urlGroup = document.querySelector("#url-input-group");
const fileGroup = document.querySelector("#file-input-group");
const operationsFieldset = document.querySelector("#operations-fieldset");

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

function setMessage(text, kind = "") {
  message.textContent = text;
  message.className = `form-message ${kind}`;
}

function renderStatus(payload) {
  const summary = payload.summary || {};
  const readiness = summary.readiness || {};
  const processing = payload.processing || {};
  document.querySelector("#module-status").textContent = processing.running
    ? `processing ${processing.completed}/${processing.total}`
    : `${payload.module_status} ${payload.module_version}`;
  const processButton = document.querySelector("#process-all");
  processButton.disabled = Boolean(processing.running);
  processButton.textContent = processing.running ? "Processing..." : "Process all sources";
  document.querySelector("#metric-module").textContent = payload.module;
  document.querySelector("#metric-sources").textContent = summary.source_count || 0;
  document.querySelector("#metric-ready").textContent = readiness.ready || 0;
  document.querySelector("#metric-partial").textContent = readiness.partial || 0;

  const rows = document.querySelector("#source-rows");
  if (!payload.sources || payload.sources.length === 0) {
    rows.innerHTML = '<tr><td colspan="5" class="empty">No sources registered yet.</td></tr>';
    return;
  }
  rows.innerHTML = payload.sources.map((source) => `
    <tr>
      <td><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(source.source_id)}</small></td>
      <td>${escapeHtml(source.kind)}</td>
      <td><div class="readiness-wrap">
        <button class="readiness ${escapeHtml(source.readiness)}" type="button" data-source-id="${escapeHtml(source.source_id)}" aria-expanded="false">${escapeHtml(source.readiness)}</button>
        <div class="artifact-popover" data-popover-for="${escapeHtml(source.source_id)}" hidden>${renderArtifacts(source)}</div>
      </div></td>
      <td>${source.available_artifact_count}/${source.artifact_count}</td>
      <td>${new Date(source.inspected_at).toLocaleString()}</td>
    </tr>`).join("");
  rows.querySelectorAll(".readiness").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const popover = rows.querySelector(`[data-popover-for="${button.dataset.sourceId}"]`);
      const wasOpen = !popover.hidden;
      rows.querySelectorAll(".artifact-popover").forEach((item) => { item.hidden = true; });
      rows.querySelectorAll(".readiness").forEach((item) => { item.setAttribute("aria-expanded", "false"); });
      popover.hidden = wasOpen;
      button.setAttribute("aria-expanded", String(!wasOpen));
    });
  });
}

function renderArtifacts(source) {
  if (!source.artifacts || source.artifacts.length === 0) {
    return '<p class="popover-empty">No artifact records yet.</p>';
  }
  return `<div class="popover-title">Artifacts</div><ul>${source.artifacts.map((artifact) => `
    <li><span class="artifact-state ${escapeHtml(artifact.state)}">${escapeHtml(artifact.state)}</span><span><strong>${escapeHtml(artifact.kind)}</strong><small>${escapeHtml(artifact.relative_path)}</small></span></li>`).join("")}</ul>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
}

async function refreshStatus() {
  const response = await fetch("/api/status");
  if (!response.ok) throw new Error("Could not load status");
  renderStatus(await response.json());
}

kindSelect.addEventListener("change", () => syncInputMode());
form.querySelectorAll("input[name='source_mode']").forEach((input) => input.addEventListener("change", () => syncInputMode()));
syncInputMode("url");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const mode = selectedMode();
  if (mode === "local") {
    data.delete("source_mode");
    data.delete("locator");
    data.delete("download_video");
    data.delete("fetch_metadata");
    data.delete("fetch_subtitles");
    setMessage("Adding local file...");
    try {
      const response = await fetch("/api/source-intake/upload", {
        method: "POST",
        body: data
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Upload failed");
      renderStatus(result.status);
      setMessage(`Added. Stored artifacts: ${result.stored_artifact_count}.`, "success");
    } catch (error) {
      setMessage(error.message, "error");
    }
    return;
  }
  const payload = {
    source_id: data.get("source_id"),
    locator: data.get("locator"),
    title: data.get("title"),
    kind: data.get("kind"),
    download_video: data.has("download_video"),
    fetch_metadata: data.has("fetch_metadata"),
    fetch_subtitles: data.has("fetch_subtitles")
  };
  setMessage("Running acquisition...");
  try {
    const response = await fetch("/api/source-intake/acquire", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Acquisition failed");
    renderStatus(result.status);
    setMessage(`Completed. Stored artifacts: ${result.stored_artifact_count}.`, "success");
  } catch (error) {
    setMessage(error.message, "error");
  }
});

document.querySelector("#refresh").addEventListener("click", () => {
  refreshStatus().catch((error) => setMessage(error.message, "error"));
});

document.querySelector("#process-all").addEventListener("click", async () => {
  if (!window.confirm("Start video, metadata and subtitle acquisition for all pending sources?")) return;
  setMessage("Starting batch processing...");
  try {
    const response = await fetch("/api/source-intake/process-all", {method: "POST"});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not start processing");
    renderStatus(await (await fetch("/api/status")).json());
    setMessage(result.message || "Batch processing started.");
  } catch (error) {
    setMessage(error.message, "error");
  }
});

document.addEventListener("click", () => {
  document.querySelectorAll(".artifact-popover").forEach((item) => { item.hidden = true; });
  document.querySelectorAll(".readiness").forEach((item) => { item.setAttribute("aria-expanded", "false"); });
});

refreshStatus().catch((error) => setMessage(error.message, "error"));
setInterval(() => refreshStatus().catch(() => {}), 4000);
