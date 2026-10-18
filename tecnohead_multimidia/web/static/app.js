const $ = (id) => document.getElementById(id);
const state = { areas: [], status: null, audio: null, selectedAreaId: null, currentArea: null, formDirty: false, audioFormDirty: false };

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

function audioZoneConfig(zoneId) { return (state.audio?.config?.zones || []).find((zone) => zone.zone_id === zoneId) || {}; }
function audioZoneStatus(zoneId) { return (state.audio?.zones || []).find((zone) => zone.zone_id === zoneId) || {}; }
function audioArea(areaId) { return (state.audio?.areas || []).find((area) => area.area_id === areaId) || {}; }
function audioStatusLabel(value) { return ({ ready: "Pronto", degraded: "Degradado", unavailable: "Indisponível", area_mismatch: "Área incompatível", unconfigured: "Não configurado" }[value] || value || "—"); }
function audioAirplayLabel(value) { return ({ not_configured: "Não configurado", blocked: "Bloqueado", not_homologated: "Não homologado", ready: "Pronto para teste", starting: "Iniciando", advertising: "Visível no AirPlay", streaming: "Recebendo áudio" }[value] || value || "Não testado"); }

function audioAreaOptions(selected) {
  return `<option value="">Selecionar área HA</option>` + (state.audio?.areas || []).map((area) => `<option value="${escapeHtml(area.area_id)}" ${area.area_id === selected ? "selected" : ""}>${escapeHtml(area.name)}</option>`).join("");
}

function audioPlayerOptions(areaId, selected) {
  const players = audioArea(areaId).media_players || [];
  return `<option value="">Selecionar media_player</option>` + players.map((entity) => `<option value="${escapeHtml(entity.entity_id)}" ${entity.entity_id === selected ? "selected" : ""}>${escapeHtml(entity.entity_id)}${entity.friendly_name ? ` — ${escapeHtml(entity.friendly_name)}` : ""}</option>`).join("");
}

function renderAudioForm() {
  if (state.audioFormDirty) return;
  const labels = { kitchen: "Cozinha", pool: "Piscina" };
  const fields = $("audio-config-fields");
  fields.innerHTML = ["kitchen", "pool"].map((zoneId) => {
    const config = audioZoneConfig(zoneId); const status = audioZoneStatus(zoneId);
    const areaId = config.area_id || status.area_id || ""; const entityId = config.media_player_entity_id || status.entity_id || "";
    const priority = config.priority || (zoneId === "pool" ? "hdmi_arc" : "normal");
    const airplay = config.airplay || {};
    return `<article class="audio-config-card" data-audio-config-zone="${zoneId}">
      <h3>${labels[zoneId]}</h3>
      <label class="check-item"><input type="checkbox" data-audio-enabled="${zoneId}" ${config.enabled || status.enabled ? "checked" : ""} /><span>Habilitar zona no TecnoHead</span></label>
      <label>Área Home Assistant<select data-audio-area="${zoneId}">${audioAreaOptions(areaId)}</select></label>
      <label>Amplificador / media_player<select data-audio-player="${zoneId}">${audioPlayerOptions(areaId, entityId)}</select></label>
      <div class="form-row two">
        <label>Limite de volume (%)<input type="number" min="0" max="100" step="1" data-audio-max="${zoneId}" value="${escapeHtml(config.max_volume_percent ?? status.max_volume_percent ?? 30)}" /></label>
        <label>Prioridade<select data-audio-priority="${zoneId}"><option value="normal" ${priority === "normal" ? "selected" : ""}>Normal</option><option value="hdmi_arc" ${priority === "hdmi_arc" ? "selected" : ""}>HDMI ARC</option></select></label>
      </div>
      <label class="check-item"><input type="checkbox" data-audio-airplay="${zoneId}" ${airplay.enabled ? "checked" : ""} /><span>Ativar receptor AirPlay 2 nesta zona</span></label>
      ${zoneId === "pool" ? `<label class="check-item"><input type="checkbox" data-audio-arc-override="${zoneId}" ${config.airplay_may_override_arc ? "checked" : ""} /><span>Permitir AirPlay substituir ARC (somente explícito)</span></label>` : ""}
      <p class="muted">${escapeHtml(status.diagnostic || "Selecione somente entidades descobertas nesta área.")}</p>
    </article>`;
  }).join("");
  fields.querySelectorAll("[data-audio-area]").forEach((select) => select.addEventListener("change", () => {
    const zoneId = select.dataset.audioArea; const player = document.querySelector(`[data-audio-player="${zoneId}"]`);
    player.innerHTML = audioPlayerOptions(select.value, ""); state.audioFormDirty = true;
  }));
  $("audio-group-strategy").value = state.audio?.config?.group_strategy || "none";
  $("audio-group-master").value = state.audio?.config?.group_master_zone_id || "";
}

function renderAudioZones() {
  const zones = (state.audio?.zones || []).filter((zone) => ["kitchen", "pool"].includes(zone.zone_id));
  $("audio-zones").innerHTML = zones.map((zone) => {
    const entity = zone.entity || {}; const supports = entity.supports || {}; const sourceList = entity.source_list || [];
    const airplayEndpoint = (state.audio?.airplay?.endpoints || {})[zone.zone_id] || {};
    const volume = entity.volume_level == null ? "não observado" : `${Math.round(Number(entity.volume_level) * 100)}%`;
    const currentSource = entity.source || "fonte não confirmada"; const metadata = [entity.media_title, entity.media_artist].filter(Boolean).join(" — "); const max = zone.max_volume_percent ?? 30;
    const volumeInput = supports.volume ? `<div class="audio-control-row"><label class="field">Volume até ${max}%<input type="number" min="0" max="${max}" step="1" value="${entity.volume_level == null ? "" : Math.min(max, Math.round(Number(entity.volume_level) * 100))}" data-audio-volume="${zone.zone_id}" placeholder="%" /></label><button type="button" class="button button-secondary audio-apply-volume" data-zone="${zone.zone_id}">Aplicar</button></div>` : `<p class="muted">A entidade não anunciou volume absoluto; nenhum slider seguro foi criado.</p>`;
    const sourceControl = supports.source ? `<div class="audio-control-row"><label class="field">Fonte<select data-audio-source="${zone.zone_id}">${sourceList.map((source) => `<option value="${escapeHtml(source)}" ${String(source).toLowerCase() === String(currentSource).toLowerCase() ? "selected" : ""}>${escapeHtml(source)}</option>`).join("")}</select></label><button type="button" class="button button-secondary audio-apply-source" data-zone="${zone.zone_id}">Trocar</button></div>` : `<p class="muted">Nenhuma lista de fontes foi anunciada.</p>`;
    const muteButton = supports.mute ? `<button type="button" class="button button-ghost audio-apply-mute" data-zone="${zone.zone_id}" data-mute="${entity.is_volume_muted ? "false" : "true"}">${entity.is_volume_muted ? "Desmutar" : "Mudo"}</button>` : "";
    const playback = supports.playback ? `<div class="audio-actions"><button type="button" class="button button-ghost audio-playback" data-zone="${zone.zone_id}" data-action="play">Reproduzir</button><button type="button" class="button button-ghost audio-playback" data-zone="${zone.zone_id}" data-action="pause">Pausar</button><button type="button" class="button button-ghost audio-playback" data-zone="${zone.zone_id}" data-action="stop">Parar</button></div>` : "";
    const airplayLine = zone.airplay?.enabled ? `<span>AirPlay 2: ${escapeHtml(audioAirplayLabel(airplayEndpoint.state || "starting"))}${airplayEndpoint.listen_port ? ` · porta ${escapeHtml(airplayEndpoint.listen_port)}` : ""}${airplayEndpoint.diagnostic ? ` · ${escapeHtml(airplayEndpoint.diagnostic)}` : ""}</span>` : `<span>AirPlay 2: desativado nesta zona</span>`;
    return `<article class="audio-zone-card"><div class="audio-zone-head"><div><p class="eyebrow">ZONA</p><h3>${escapeHtml(zone.label)}</h3></div><span class="audio-state ${escapeHtml(zone.status)}">${escapeHtml(audioStatusLabel(zone.status))}</span></div><div class="audio-meta"><span>Entidade: <code>${escapeHtml(zone.entity_id || "não selecionada")}</code></span><span>Fonte: ${escapeHtml(currentSource)} · Volume: ${escapeHtml(volume)}</span>${metadata ? `<span>Reproduzindo: ${escapeHtml(metadata)}</span>` : ""}<span>${escapeHtml(zone.diagnostic || "")}</span>${airplayLine}${zone.priority === "hdmi_arc" ? `<span class="audio-notice warning">TV/HDMI ARC tem prioridade. O App não troca a fonte automaticamente.</span>` : ""}</div><div class="audio-controls">${volumeInput}${sourceControl}${playback}<div class="audio-actions">${muteButton}</div></div></article>`;
  }).join("");
  $("audio-group-state").textContent = state.audio?.config?.group_strategy && state.audio.config.group_strategy !== "none" ? `Estratégia: ${state.audio.config.group_strategy} · líder: ${state.audio.config.group_master_zone_id || "—"}` : "Nenhum grupo solicitado";
  const airplay = state.audio?.airplay || {}; const airplayState = $("audio-airplay-state");
  airplayState.textContent = audioAirplayLabel(airplay.state); airplayState.className = `hint audio-state ${airplay.state || ""}`;
  const endpointSummary = Object.entries(airplay.endpoints || {}).map(([zoneId, endpoint]) => `${zoneId}: ${audioAirplayLabel(endpoint.state)}`).join(" · ");
  $("audio-airplay-details").textContent = `${airplay.reason || "Aguardando descoberta."} Shairport: ${airplay.shairport_sync || "—"}; NQPTP: ${airplay.nqptp || "—"}; endpoints: ${endpointSummary || "nenhum"}; áudio físico: ${airplay.physical_audio || "—"}.`;
  const overall = $("audio-overall-state"); const configured = zones.filter((zone) => zone.enabled).length;
  overall.textContent = airplay.state === "blocked" ? "Áudio físico pendente" : configured ? `${configured} zona(s) cadastrada(s)` : "Não configurado";
  overall.className = `mode-chip ${airplay.state === "blocked" ? "tv" : configured ? "cinema" : "off"}`;
  document.querySelectorAll(".audio-apply-volume").forEach((button) => button.addEventListener("click", () => applyAudioVolume(button.dataset.zone)));
  document.querySelectorAll(".audio-apply-mute").forEach((button) => button.addEventListener("click", () => applyAudioMute(button.dataset.zone, button.dataset.mute === "true")));
  document.querySelectorAll(".audio-apply-source").forEach((button) => button.addEventListener("click", () => applyAudioSource(button.dataset.zone)));
  document.querySelectorAll(".audio-playback").forEach((button) => button.addEventListener("click", () => applyAudioPlayback(button.dataset.zone, button.dataset.action)));
}

function renderAudio() { if (!state.audio) return; renderAudioZones(); renderAudioForm(); }

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
  // The status poll runs every few seconds. Do not overwrite an in-progress
  // commissioning form with the last persisted profile while the user edits.
  if (state.selectedAreaId && !state.formDirty) loadProfile(state.selectedAreaId);
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
  state.formDirty = false;
  try {
    state.currentArea = await api(`api/areas/${encodeURIComponent(areaId)}`);
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
  try { const profile = await api(`api/areas/${encodeURIComponent(state.selectedAreaId)}`, { method: "PUT", body: JSON.stringify(buildProfile()) }); state.currentArea.profile = profile; state.formDirty = false; message.textContent = "Perfil salvo com validação de domínio e área."; toast("Perfil salvo"); await loadAll(false); } catch (error) { state.formDirty = true; message.textContent = `Falha: ${error.message}`; toast(error.message); }
}

async function setMode(areaId, mode) {
  try { await api(`api/areas/${encodeURIComponent(areaId)}/mode`, { method: "POST", body: JSON.stringify({ mode, confirmed: true }) }); toast(`Cena ${modeLabel(mode)} iniciada`); setTimeout(() => loadAll(false), 900); } catch (error) { toast(`Cena não iniciada: ${error.message}`); }
}

async function testIr(direction) {
  if (!confirm(`Enviar o preset IR ${direction.toUpperCase()} agora? Isso pode atuar fisicamente no projetor.`)) return;
  try { const result = await api(`api/areas/${encodeURIComponent(state.selectedAreaId)}/ir/test`, { method: "POST", body: JSON.stringify({ direction, confirmed: true }) }); toast(`HA aceitou ${result.calls?.length || 1} chamada(s); resposta física ainda não é observável.`); await loadProfile(state.selectedAreaId); } catch (error) { toast(`Teste IR: ${error.message}`); }
}

async function checkRemote() {
  try {
    const result = await api(`api/areas/${encodeURIComponent(state.selectedAreaId)}/ir/check`);
    const label = result.friendly_name ? ` — ${result.friendly_name}` : "";
    toast(`Entidade ${result.entity_id}${label} validada na área; nenhum IR foi emitido.`);
  } catch (error) { toast(`Validação da entidade: ${error.message}`); }
}

async function restoreIr() {
  if (!confirm("Restaurar os presets ON/OFF autorizados e os padrões ON1/OFF2/5s?")) return;
  try { await api(`api/areas/${encodeURIComponent(state.selectedAreaId)}/ir/restore`, { method: "POST", body: JSON.stringify({ confirmed: true }) }); toast("Presets restaurados"); await loadProfile(state.selectedAreaId); } catch (error) { toast(error.message); }
}

function audioBaseZone(zoneId) {
  return audioZoneConfig(zoneId) || {};
}

function buildAudioConfig() {
  const labels = { kitchen: "Cozinha", pool: "Piscina" };
  const zones = ["kitchen", "pool"].map((zoneId) => {
    const base = audioBaseZone(zoneId); const status = audioZoneStatus(zoneId); const area = document.querySelector(`[data-audio-area="${zoneId}"]`).value || null;
    const player = document.querySelector(`[data-audio-player="${zoneId}"]`).value || null; const oldAirplay = base.airplay || {};
    const stableId = oldAirplay.stable_id || (crypto.randomUUID ? crypto.randomUUID().replaceAll("-", "") : `${zoneId}-${Date.now()}`);
    return { zone_id: zoneId, area_id: area, enabled: document.querySelector(`[data-audio-enabled="${zoneId}"]`).checked, media_player_entity_id: player, max_volume_percent: Number(document.querySelector(`[data-audio-max="${zoneId}"]`).value || 30), allow_absolute_volume: base.allow_absolute_volume || false, priority: document.querySelector(`[data-audio-priority="${zoneId}"]`).value, airplay_may_override_arc: !!document.querySelector(`[data-audio-arc-override="${zoneId}"]`)?.checked, airplay: { ...oldAirplay, enabled: !!document.querySelector(`[data-audio-airplay="${zoneId}"]`).checked, service_name: oldAirplay.service_name || `TecnoHead ${labels[zoneId]}`, stable_id: stableId, output_backend: oldAirplay.output_backend || "pcm_bridge", pairing_state: oldAirplay.pairing_state || "not_configured" } };
  });
  const strategy = $("audio-group-strategy").value; const master = $("audio-group-master").value.trim() || null; const old = state.audio?.config || {};
  return { enabled: zones.some((zone) => zone.enabled), zones, group_strategy: strategy, group_master_zone_id: master, members: strategy === "none" ? [] : (old.members || []), share_pool_tv_to_kitchen: !!old.share_pool_tv_to_kitchen };
}

async function saveAudio(event) {
  event.preventDefault(); const message = $("audio-form-message"); message.textContent = "Validando áreas, domínio e capacidades…";
  try { await api("api/audio", { method: "PUT", body: JSON.stringify(buildAudioConfig()) }); state.audioFormDirty = false; message.textContent = "Zonas salvas com validação estrita por área."; toast("Configuração de áudio salva"); await loadAll(false); } catch (error) { state.audioFormDirty = true; message.textContent = `Falha: ${error.message}`; toast(`Áudio: ${error.message}`); }
}

async function applyAudioVolume(zoneId) {
  const input = document.querySelector(`[data-audio-volume="${zoneId}"]`); const value = Number(input?.value);
  if (!Number.isFinite(value)) { toast("Informe um volume válido."); return; }
  if (!confirm(`Aplicar volume ${value}% na zona ${audioZoneStatus(zoneId).label || zoneId}?`)) return;
  try { await api(`api/audio/zones/${encodeURIComponent(zoneId)}/volume`, { method: "POST", body: JSON.stringify({ volume_percent: value, confirmed: true }) }); toast("Volume enviado ao Home Assistant; confirmação física depende do player."); await loadAll(false); } catch (error) { toast(`Volume: ${error.message}`); }
}

async function applyAudioMute(zoneId, muted) {
  if (!confirm(`${muted ? "Ativar" : "Desativar"} mudo na zona ${audioZoneStatus(zoneId).label || zoneId}?`)) return;
  try { await api(`api/audio/zones/${encodeURIComponent(zoneId)}/mute`, { method: "POST", body: JSON.stringify({ is_volume_muted: muted, confirmed: true }) }); toast("Mudo enviado ao Home Assistant."); await loadAll(false); } catch (error) { toast(`Mudo: ${error.message}`); }
}

async function applyAudioSource(zoneId) {
  const source = document.querySelector(`[data-audio-source="${zoneId}"]`)?.value; if (!source) return;
  if (!confirm(`Trocar a fonte da zona ${audioZoneStatus(zoneId).label || zoneId} para “${source}”?`)) return;
  try { await api(`api/audio/zones/${encodeURIComponent(zoneId)}/source`, { method: "POST", body: JSON.stringify({ source, confirmed: true }) }); toast("Fonte enviada ao Home Assistant; estado será reavaliado."); await loadAll(false); } catch (error) { toast(`Fonte: ${error.message}`); }
}

async function applyAudioPlayback(zoneId, action) {
  if (!confirm(`${action === "play" ? "Reproduzir" : action === "pause" ? "Pausar" : "Parar"} na zona ${audioZoneStatus(zoneId).label || zoneId}?`)) return;
  try { await api(`api/audio/zones/${encodeURIComponent(zoneId)}/playback`, { method: "POST", body: JSON.stringify({ action, confirmed: true }) }); toast("Ação de reprodução enviada ao Home Assistant."); await loadAll(false); } catch (error) { toast(`Reprodução: ${error.message}`); }
}

async function sharePoolToKitchen() {
  if (!confirm("Compartilhar a fonte atual da Piscina com a Cozinha pelo grupo do Home Assistant? A TV/ARC da Piscina permanece líder; isso pode interromper a fonte atual da Cozinha.")) return;
  try { await api("api/audio/group/share-pool-to-kitchen", { method: "POST", body: JSON.stringify({ confirmed: true }) }); toast("Agrupamento solicitado; confirme o áudio fisicamente."); await loadAll(false); } catch (error) { toast(`Grupo: ${error.message}`); }
}

async function unjoinPool() {
  if (!confirm("Separar o grupo da Piscina? O App não altera HDMI ARC/CEC.")) return;
  try { await api("api/audio/group/pool/unjoin", { method: "POST", body: JSON.stringify({ confirmed: true }) }); toast("Separação solicitada ao Home Assistant."); await loadAll(false); } catch (error) { toast(`Separação: ${error.message}`); }
}

function renderEvents() {
  const events = state.status?.events || [];
  $("events").innerHTML = events.length ? events.slice().reverse().map((event) => `<div class="event ${escapeHtml(event.level)}"><div class="event-top"><span>${escapeHtml(event.event)}</span><time>${new Date(event.timestamp).toLocaleTimeString("pt-BR")}</time></div><div class="event-message">${escapeHtml(event.message)}</div></div>`).join("") : `<div class="empty-state">Sem eventos ainda.</div>`;
}

async function loadAll(refresh = false) {
  try { [state.status, state.areas, state.audio] = await Promise.all([api("api/status"), api(`api/areas?refresh=${refresh}`), api("api/audio")]); renderStatus(); renderCards(); renderAreasSelect(); renderAudio(); renderEvents(); } catch (error) { toast(`Descoberta: ${error.message}`); renderStatus(); renderEvents(); }
}

$("refresh").addEventListener("click", () => loadAll(true));
$("area-select").addEventListener("change", (event) => loadProfile(event.target.value));
$("area-form").addEventListener("submit", saveProfile);
$("area-form").addEventListener("input", () => { state.formDirty = true; });
$("area-form").addEventListener("change", () => { state.formDirty = true; });
$("audio-form").addEventListener("submit", saveAudio);
$("audio-form").addEventListener("input", () => { state.audioFormDirty = true; });
$("audio-form").addEventListener("change", () => { state.audioFormDirty = true; });
$("audio-share-pool").addEventListener("click", sharePoolToKitchen);
$("audio-unjoin-pool").addEventListener("click", unjoinPool);
$("audio-refresh").addEventListener("click", async () => { state.audioFormDirty = false; await loadAll(true); });
$("reload-profile").addEventListener("click", () => loadProfile(state.selectedAreaId));
$("remote-entity").addEventListener("change", () => renderRemoteHint(state.currentArea?.profile || {}));
$("climate-entity").addEventListener("change", () => renderClimateOptions(state.currentArea?.profile || {}));
$("test-ir-on").addEventListener("click", () => testIr("on")); $("test-ir-off").addEventListener("click", () => testIr("off")); $("restore-ir").addEventListener("click", restoreIr);
$("check-remote").addEventListener("click", checkRemote);
$("download-diagnostics").addEventListener("click", async () => { try { const data = await api("api/diagnostics"); const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "tecnohead-diagnostics-redacted.json"; link.click(); URL.revokeObjectURL(link.href); } catch (error) { toast(error.message); } });
loadAll(true); setInterval(() => loadAll(false), 5000);
