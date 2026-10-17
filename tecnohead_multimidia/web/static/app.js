const $ = (id) => document.getElementById(id);
const state = { areas: [], status: null, selectedAreaId: null, currentArea: null };

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!response.ok) throw new Error(data?.detail || data || `HTTP ${response.status}`);
  return data;
}

function toast(message) {
  const node = $("toast"); node.textContent = message; node.classList.add("show");
  clearTimeout(toast.timer); toast.timer = setTimeout(() => node.classList.remove("show"), 3600);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function modeLabel(value) { return ({ off: "Desligado", cinema: "Cinema", tv: "TV" }[value] || value || "—"); }
function phaseLabel(value) { return ({ idle: "Pronto", starting: "Iniciando", active: "Ativo", stopping: "Desligando", error: "Degradado", uncertain: "UNCERTAIN" }[value] || value || "—"); }
function selectedEngine(areaId) { return (state.status?.areas || []).find((item) => item.area_id === areaId) || {}; }

function renderStatus() {
  const status = state.status || {};
  $("app-version").textContent = `v${status.app_version || "—"}`;
  const ha = status.home_assistant || {};
  const pill = $("ha-state"); pill.textContent = ha.available ? "HAOS online" : "HAOS offline"; pill.className = `status-pill ${ha.available ? "online" : "offline"}`;
  $("last-discovery").textContent = ha.last_discovery ? `Última descoberta: ${new Date(ha.last_discovery * 1000).toLocaleTimeString("pt-BR")}` : "Descoberta não executada";
  const mqtt = status.mqtt || {};
  $("diagnostic-summary").innerHTML = [
    ["Home Assistant", ha.available ? "Disponível" : (ha.last_error || "Indisponível")],
    ["MQTT Discovery", mqtt.connected ? "Conectado" : (mqtt.last_error || "Aguardando broker")],
    ["Áreas habilitadas", String((status.areas || []).length)],
  ].map(([key, value]) => `<div class="diagnostic-tile"><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
}

function renderCards() {
  const container = $("area-cards");
  if (!state.areas.length) { container.innerHTML = `<div class="empty-state">Nenhuma área registrada foi retornada pelo Home Assistant.</div>`; return; }
  container.innerHTML = state.areas.map((area) => {
    const engine = selectedEngine(area.area_id);
    const profile = area.profile;
    const configured = profile?.enabled;
    const mode = engine.mode || "off";
    return `<article class="area-card">
      <div class="area-card-head"><div><p class="eyebrow">ÁREA HA</p><h3>${escapeHtml(area.name)}</h3></div><span class="mode-chip ${escapeHtml(mode)}">${escapeHtml(modeLabel(mode))}</span></div>
      <div class="card-meta"><span class="phase">${escapeHtml(phaseLabel(engine.phase))}</span><span>${configured ? "Perfil habilitado" : "Não configurada"}</span></div>
      <div class="scene-buttons"><button class="button button-primary scene-action" data-area="${escapeHtml(area.area_id)}" data-mode="cinema">Cinema</button><button class="button button-secondary scene-action" data-area="${escapeHtml(area.area_id)}" data-mode="tv">TV</button><button class="button button-dark scene-action" data-area="${escapeHtml(area.area_id)}" data-mode="off">Desligar</button></div>
    </article>`;
  }).join("");
  document.querySelectorAll(".scene-action").forEach((button) => button.addEventListener("click", () => setMode(button.dataset.area, button.dataset.mode)));
}

function renderAreasSelect() {
  const select = $("area-select");
  select.innerHTML = state.areas.map((area) => `<option value="${escapeHtml(area.area_id)}">${escapeHtml(area.name)}</option>`).join("");
  if (state.selectedAreaId && state.areas.some((area) => area.area_id === state.selectedAreaId)) select.value = state.selectedAreaId;
  else state.selectedAreaId = select.value || null;
  if (state.selectedAreaId) loadProfile(state.selectedAreaId);
}

function populateSelect(id, entities, predicate, selected, blank = "Não configurado") {
  const select = $(id);
  const candidates = entities.filter(predicate);
  select.innerHTML = `<option value="">${escapeHtml(blank)}</option>` + candidates.map((entity) => `<option value="${escapeHtml(entity.entity_id)}">${escapeHtml(entity.entity_id)}${entity.friendly_name ? ` — ${escapeHtml(entity.friendly_name)}` : ""}</option>`).join("");
  select.value = selected || "";
  return candidates;
}

function selectedEntity(id) { return (state.currentArea?.entities || []).find((entity) => entity.entity_id === $(id).value); }

function renderClimateOptions(profile) {
  const climate = selectedEntity("climate-entity");
  const attrs = climate?.attributes || {};
  const fill = (id, values, selected) => { const select = $(id); const unique = [...new Set((values || []).map(String))]; select.innerHTML = `<option value="">Detectar da entidade</option>` + unique.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join(""); select.value = selected || ""; };
  fill("low-fan", attrs.fan_modes, profile.climate?.low_fan_mode);
  fill("high-fan", attrs.fan_modes, profile.climate?.high_fan_mode);
  fill("vane-mode", attrs.swing_modes || attrs.vane_modes, profile.climate?.vane_mode);
}

function renderLighting(profile) {
  const entities = state.currentArea?.entities || [];
  const lights = entities.filter((entity) => entity.domain === "light");
  const switches = entities.filter((entity) => entity.domain === "switch");
  const selected = new Set(profile.lighting_switch_entity_ids || []);
  $("lighting-list").innerHTML = [...lights.map((entity) => `<div class="check-item"><input type="checkbox" checked disabled /><span>${escapeHtml(entity.entity_id)} <small>(light automática)</small></span></div>`), ...switches.map((entity) => `<label class="check-item"><input type="checkbox" data-light-switch="${escapeHtml(entity.entity_id)}" ${selected.has(entity.entity_id) ? "checked" : ""} /><span>${escapeHtml(entity.entity_id)} <small>(classificar como luz)</small></label>`)].join("") || `<span class="muted">Nenhuma luz foi encontrada na área.</span>`;
}

function renderRemoteHint(profile) {
  const remote = $("remote-entity").value;
  const exact = remote === "remote.ir_cinema";
  $("remote-hint").innerHTML = remote ? (exact ? `<strong>Sugestão validada:</strong> remote.ir_cinema está associada à área retornada pelo Home Assistant.` : `Remote restrito à área atual: ${escapeHtml(remote)}. O App revalida a associação antes de cada comando.`) : "Nenhum emissor foi selecionado; cenas com projetor permanecerão degradadas.";
}

async function loadProfile(areaId) {
  state.selectedAreaId = areaId;
  try {
    state.currentArea = await api(`/api/areas/${encodeURIComponent(areaId)}`);
    const area = state.currentArea; const profile = area.profile || {};
    $("editor-empty").classList.add("hidden"); $("area-form").classList.remove("hidden");
    $("enabled").value = String(!!profile.enabled); $("default-mode").value = profile.default_mode || "tv";
    const entities = area.entities || [];
    populateSelect("tv-entity", entities, (e) => e.roles?.includes("tv_candidate"), profile.tv_entity_id);
    populateSelect("receiver-entity", entities, (e) => e.roles?.includes("receiver_candidate"), profile.receiver_entity_id);
    populateSelect("screen-entity", entities, (e) => e.roles?.includes("screen_candidate"), profile.screen_entity_id);
    populateSelect("apple-entity", entities, (e) => e.domain === "media_player", profile.apple_tv_entity_id);
    populateSelect("climate-entity", entities, (e) => e.domain === "climate", profile.climate_entity_id);
    populateSelect("temperature-sensor", entities, (e) => e.domain === "sensor", profile.climate?.temperature_sensor_entity_id);
    const remotes = populateSelect("remote-entity", entities, (e) => e.domain === "remote", profile.ir?.remote_entity_id);
    if (!profile.ir?.remote_entity_id && remotes.some((e) => e.entity_id === "remote.ir_cinema")) $("remote-entity").value = "remote.ir_cinema";
    $("cinema-source").value = profile.receiver_cinema_source || ""; $("tv-source").value = profile.receiver_tv_source || "TV Audio";
    $("cinema-volume").value = profile.volume_cinema ?? 0.25; $("tv-volume").value = profile.volume_tv ?? 0.2; $("lights-delay").value = profile.lights_delay_seconds ?? 30;
    const ir = profile.ir || {}; $("command-format").value = ir.on?.format || "broadlink_b64"; $("ir-on").value = ir.on?.value || ""; $("ir-off").value = ir.off?.value || ""; $("on-sends").value = ir.on_sends ?? 1; $("off-sends").value = ir.off_sends ?? 2; $("off-interval").value = ir.off_interval_seconds ?? 5; $("on-interval").value = ir.on_interval_seconds ?? .4;
    $("setpoint").value = profile.climate?.setpoint_c ?? 22; $("high-threshold").value = profile.climate?.high_threshold_c ?? 23; $("tv-protection").value = String(profile.tv_protection_during_cinema !== false);
    renderClimateOptions(profile); renderLighting(profile); renderRemoteHint(profile);
  } catch (error) { toast(`Não foi possível carregar a área: ${error.message}`); }
}

function buildProfile() {
  const old = state.currentArea?.profile || {}; const format = $("command-format").value;
  return {
    enabled: $("enabled").value === "true", default_mode: $("default-mode").value,
    tv_entity_id: $("tv-entity").value || null, receiver_entity_id: $("receiver-entity").value || null, screen_entity_id: $("screen-entity").value || null, apple_tv_entity_id: $("apple-entity").value || null, climate_entity_id: $("climate-entity").value || null,
    lighting_switch_entity_ids: [...document.querySelectorAll("[data-light-switch]:checked")].map((node) => node.dataset.lightSwitch),
    receiver_cinema_source: $("cinema-source").value.trim() || null, receiver_tv_source: $("tv-source").value.trim() || null, volume_cinema: Number($("cinema-volume").value || .25), volume_tv: Number($("tv-volume").value || .2), lights_delay_seconds: Number($("lights-delay").value || 30), tv_protection_during_cinema: $("tv-protection").value === "true", tv_protection_action: "turn_off",
    climate: { ...(old.climate || {}), enabled: true, setpoint_c: Number($("setpoint").value || 22), high_threshold_c: Number($("high-threshold").value || 23), low_fan_mode: $("low-fan").value || null, high_fan_mode: $("high-fan").value || null, vane_mode: $("vane-mode").value || null, temperature_sensor_entity_id: $("temperature-sensor").value || null },
    ir: { ...(old.ir || {}), remote_entity_id: $("remote-entity").value || null, on: { format, value: $("ir-on").value.trim() }, off: { format, value: $("ir-off").value.trim() }, on_sends: Number($("on-sends").value || 1), off_sends: Number($("off-sends").value || 2), on_interval_seconds: Number($("on-interval").value || .4), off_interval_seconds: Number($("off-interval").value || 5) },
  };
}

async function saveProfile(event) {
  event.preventDefault(); const message = $("form-message"); message.textContent = "Validando áreas e salvando…";
  try { const profile = await api(`/api/areas/${encodeURIComponent(state.selectedAreaId)}`, { method: "PUT", body: JSON.stringify(buildProfile()) }); state.currentArea.profile = profile; message.textContent = "Perfil salvo com validação de domínio e área."; toast("Perfil salvo"); await loadAll(false); } catch (error) { message.textContent = `Falha: ${error.message}`; toast(error.message); }
}

async function setMode(areaId, mode) {
  try { await api(`/api/areas/${encodeURIComponent(areaId)}/mode`, { method: "POST", body: JSON.stringify({ mode, confirmed: true }) }); toast(`Cena ${modeLabel(mode)} iniciada`); setTimeout(() => loadAll(false), 900); } catch (error) { toast(`Cena não iniciada: ${error.message}`); }
}

async function testIr(direction) {
  if (!confirm(`Enviar o preset IR ${direction.toUpperCase()} agora? Isso pode atuar fisicamente no projetor.`)) return;
  try { const result = await api(`/api/areas/${encodeURIComponent(state.selectedAreaId)}/ir/test`, { method: "POST", body: JSON.stringify({ direction, confirmed: true }) }); toast(`HA aceitou ${result.calls?.length || 1} chamada(s); resposta física ainda não é observável.`); await loadProfile(state.selectedAreaId); } catch (error) { toast(`Teste IR: ${error.message}`); }
}

async function restoreIr() {
  if (!confirm("Restaurar os presets ON/OFF autorizados e os padrões ON1/OFF2/5s?")) return;
  try { await api(`/api/areas/${encodeURIComponent(state.selectedAreaId)}/ir/restore`, { method: "POST", body: JSON.stringify({ confirmed: true }) }); toast("Presets restaurados"); await loadProfile(state.selectedAreaId); } catch (error) { toast(error.message); }
}

function renderEvents() {
  const events = state.status?.events || [];
  $("events").innerHTML = events.length ? events.slice().reverse().map((event) => `<div class="event ${escapeHtml(event.level)}"><div class="event-top"><span>${escapeHtml(event.event)}</span><time>${new Date(event.timestamp).toLocaleTimeString("pt-BR")}</time></div><div class="event-message">${escapeHtml(event.message)}</div></div>`).join("") : `<div class="empty-state">Sem eventos ainda.</div>`;
}

async function loadAll(refresh = false) {
  try { [state.status, state.areas] = await Promise.all([api("/api/status"), api(`/api/areas?refresh=${refresh}`)]); renderStatus(); renderCards(); renderAreasSelect(); renderEvents(); } catch (error) { toast(`Descoberta: ${error.message}`); renderStatus(); renderEvents(); }
}

$("refresh").addEventListener("click", () => loadAll(true));
$("area-select").addEventListener("change", (event) => loadProfile(event.target.value));
$("area-form").addEventListener("submit", saveProfile);
$("reload-profile").addEventListener("click", () => loadProfile(state.selectedAreaId));
$("remote-entity").addEventListener("change", () => renderRemoteHint(state.currentArea?.profile || {}));
$("climate-entity").addEventListener("change", () => renderClimateOptions(state.currentArea?.profile || {}));
$("test-ir-on").addEventListener("click", () => testIr("on")); $("test-ir-off").addEventListener("click", () => testIr("off")); $("restore-ir").addEventListener("click", restoreIr);
$("download-diagnostics").addEventListener("click", async () => { try { const data = await api("/api/diagnostics"); const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "tecnohead-diagnostics-redacted.json"; link.click(); URL.revokeObjectURL(link.href); } catch (error) { toast(error.message); } });
loadAll(true); setInterval(() => loadAll(false), 5000);
