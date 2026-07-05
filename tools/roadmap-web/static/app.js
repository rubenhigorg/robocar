/* Roadmap Robocar — frontend vanilla. Estado en el servidor (SQLite). */
const $ = (sel, el = document) => el.querySelector(sel);
const STATUS_CYCLE = ["pending", "in_progress", "done"];
const STATUS_LABEL = { pending: "Pendiente", in_progress: "En curso", done: "Hecho" };
const DSTATUS_CYCLE = ["open", "planned", "closed"];
const DSTATUS_LABEL = { open: "Abierta", planned: "Prevista", closed: "Cerrada" };

let state = null;

/* ---------- identidad y clave ---------- */
const getKey = () => localStorage.getItem("roadmap_key") || "";
const getName = () => localStorage.getItem("roadmap_name") || "";

function askName() {
  const n = prompt("¿Tu nombre? (aparecerá en el historial)", getName() || "Rubén");
  if (n) localStorage.setItem("roadmap_name", n.trim());
  renderWho();
  return getName();
}
function askKey() {
  const k = prompt("Clave de edición (sin ella la web es solo lectura):", "");
  if (k !== null) localStorage.setItem("roadmap_key", k.trim());
}
function renderWho() {
  $("#who").textContent = getName() ? `👤 ${getName()}` : "👤 (pon tu nombre)";
}
$("#who").addEventListener("click", askName);
$("#keyBtn").addEventListener("click", () => { askKey(); toast("Clave guardada en este navegador"); });

/* ---------- API ---------- */
async function api(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getKey()}`,
      "X-Actor": getName(),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    toast("Necesitas la clave de edición (botón 🔑)", true);
    throw new Error("auth");
  }
  if (!res.ok) { toast("Error del servidor", true); throw new Error(res.statusText); }
  return res.json();
}
const load = async () => { state = await (await fetch("api/state")).json(); render(); };

async function mutate(method, path, body) {
  if (!getName()) askName();
  await api(method, path, body);
  await load();
}

/* ---------- render ---------- */
function pct(tasks) {
  if (!tasks.length) return 0;
  return Math.round(100 * tasks.filter(t => t.status === "done").length / tasks.length);
}

/* ---------- dependencias ---------- */
const taskById = id => state.tasks.find(t => t.id === id);
const depsOf = id => (state.deps || []).filter(d => d.task_id === id).map(d => d.depends_on_id);
const isBlocked = t =>
  t.status !== "done" &&
  depsOf(t.id).some(id => { const d = taskById(id); return d && d.status !== "done"; });

function pickTask(excludeId) {
  // Selector simple: lista numerada por capa → el usuario teclea el id.
  const lines = [];
  for (const l of state.layers) {
    const lt = state.tasks.filter(t => t.layer_id === l.id);
    if (!lt.length) continue;
    lines.push(`— ${l.title.split("—")[0].trim()} —`);
    for (const t of lt) if (t.id !== excludeId) lines.push(`  ${t.id}: ${t.title.slice(0, 48)}`);
  }
  const v = prompt("¿De qué tarea depende? Escribe su nº:\n\n" + lines.join("\n"));
  const id = parseInt(v, 10);
  return Number.isFinite(id) ? id : null;
}

/* ---------- filtros (persona / estado), persistidos en el navegador ---------- */
function getFilters() { try { return JSON.parse(localStorage.getItem("roadmap_filters")) || {}; } catch { return {}; } }
function setFilters(f) { localStorage.setItem("roadmap_filters", JSON.stringify(f)); render(); }
function taskMatches(t) {
  const f = getFilters();
  if (f.who) {
    if (f.who === "(sin)") { if (t.assignee) return false; }
    else if (!(t.assignee || "").toLowerCase().includes(f.who.toLowerCase())) return false;
  }
  if (f.st && t.status !== f.st) return false;
  return true;
}
function getCollapsed() { try { return new Set(JSON.parse(localStorage.getItem("roadmap_collapsed")) || []); } catch { return new Set(); } }

/* ---------- planificación auto-programada (camino crítico por deps) ---------- */
const DAY = 86400000;
const fmtDate = ts => new Date(ts).toLocaleDateString("es-ES", { day: "2-digit", month: "short" });

function computeSchedule() {
  const dmap = {};
  (state.deps || []).forEach(d => (dmap[d.task_id] = dmap[d.task_id] || []).push(d.depends_on_id));
  const byId = {}; state.tasks.forEach(t => byId[t.id] = t);
  const memo = {}, now = Date.now();
  function calc(id, seen) {
    if (memo[id]) return memo[id];
    seen = seen || new Set();
    if (seen.has(id) || !byId[id]) return { s: now, f: now };
    seen.add(id);
    const t = byId[id];
    const est = Math.max(t.estimate_days || 1, 0.25) * DAY;
    if (t.status === "done") {
      const f = t.done_at ? t.done_at * 1000 : now;
      return memo[id] = { s: f - est, f, done: true };
    }
    // inicio = hoy, o la fecha fija manual, o el fin de la última dependencia pendiente
    let s = now;
    if (t.start_date) { const m = Date.parse(t.start_date); if (m) s = Math.max(s, m); }
    for (const d of (dmap[id] || [])) { const r = calc(d, seen); if (!r.done) s = Math.max(s, r.f); }
    let f = s + est;
    if (t.due_date) { const m = Date.parse(t.due_date); if (m) f = Math.max(s + DAY / 4, m + DAY); }
    return memo[id] = { s, f };
  }
  state.tasks.forEach(t => calc(t.id));
  // camino crítico: la cadena que fija el fin más tardío del proyecto
  const crit = new Set();
  let cur = null, maxF = -1;
  for (const t of state.tasks) {
    const m = memo[t.id];
    if (t.status !== "done" && m && m.f > maxF) { maxF = m.f; cur = t.id; }
  }
  while (cur != null && !crit.has(cur)) {
    crit.add(cur);
    let next = null, bestF = -1;
    for (const d of (dmap[cur] || [])) {
      const m = memo[d];
      if (m && !m.done && m.f > bestF) { bestF = m.f; next = d; }
    }
    cur = next;
  }
  return { sched: memo, crit, projectEnd: maxF > 0 ? maxF : null };
}

/* ---------- Gantt (SVG, sin librerías) ---------- */
function renderGantt(plan) {
  const host = $("#gantt");
  if (!host) return;
  const rows = state.tasks.filter(t => taskMatches(t) && plan.sched[t.id])
    .sort((a, b) => plan.sched[a.id].s - plan.sched[b.id].s);
  if (!rows.length) { host.innerHTML = '<div class="muted">sin tareas que mostrar</div>'; return; }
  const now = Date.now();
  const min = Math.min(now, ...rows.map(t => plan.sched[t.id].s)) - DAY;
  const max = Math.max(now, ...rows.map(t => plan.sched[t.id].f)) + DAY;
  const PXD = 26, LBL = 215, RH = 24, HDR = 28;
  const days = Math.ceil((max - min) / DAY);
  const W = LBL + days * PXD, H = HDR + rows.length * RH + 8;
  const x = ts => LBL + (ts - min) / DAY * PXD;
  let svg = "";
  for (let d = 0; d <= days; d++) {
    const ts = min + d * DAY, dt = new Date(ts), wd = dt.getDay(), gx = LBL + d * PXD;
    if (wd === 0 || wd === 6) svg += `<rect x="${gx}" y="${HDR}" width="${PXD}" height="${H - HDR}" fill="#141a28" opacity="0.6"/>`;
    if (wd === 1) svg += `<line x1="${gx}" y1="${HDR - 6}" x2="${gx}" y2="${H}" stroke="#1c2333"/>` +
      `<text x="${gx + 3}" y="${HDR - 12}" fill="#8a93a6" font-size="10">${dt.getDate()}/${dt.getMonth() + 1}</text>`;
  }
  svg += `<line x1="${x(now)}" y1="${HDR - 6}" x2="${x(now)}" y2="${H}" stroke="#5aa2ff" stroke-width="1.5" stroke-dasharray="4 3"/>` +
         `<text x="${x(now) + 4}" y="${HDR}" fill="#5aa2ff" font-size="10">HOY</text>`;
  rows.forEach((t, i) => {
    const m = plan.sched[t.id], y = HDR + i * RH + 4;
    const c = t.status === "done" ? "#3fb96b" : t.status === "in_progress" ? "#e0a83c" : isBlocked(t) ? "#5c6577" : "#5aa2ff";
    const isCrit = plan.crit.has(t.id);
    const label = t.title.length > 31 ? t.title.slice(0, 30) + "…" : t.title;
    svg += `<text x="4" y="${y + 12}" fill="${t.status === "done" ? "#8a93a6" : "#e8ecf4"}" font-size="11">${esc(label)}</text>`;
    svg += `<rect x="${x(m.s)}" y="${y}" width="${Math.max(x(m.f) - x(m.s), 5)}" height="15" rx="4" fill="${c}" opacity="${t.status === "done" ? 0.5 : 0.9}"${isCrit ? ' stroke="#e05c5c" stroke-width="1.8"' : ""}>` +
      `<title>${esc(t.title)} — ${fmtDate(m.s)} → ${fmtDate(m.f)} (~${t.estimate_days || 1}d)${isCrit ? " · CAMINO CRÍTICO" : ""}</title></rect>`;
    if (t.assignee) svg += `<text x="${x(m.f) + 5}" y="${y + 12}" fill="#8a93a6" font-size="10">${esc(t.assignee.slice(0, 14))}</text>`;
  });
  const end = plan.projectEnd ? `fin estimado del proyecto: <b>${fmtDate(plan.projectEnd)}</b> · ` : "";
  host.innerHTML = `<div class="muted small" style="margin-bottom:6px">${end}borde rojo = camino crítico · hechas con fechas reales · clic en ~Nd de una tarea para estimar</div>` +
    `<div class="graph-wrap"><svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${svg}</svg></div>`;
}

/* ---------- diagrama de dependencias (SVG, sin librerías) ---------- */
function renderDepGraph(plan) {
  const host = $("#depGraph");
  if (!host) return;
  const deps = state.deps || [];
  if (!deps.length) { host.innerHTML = '<div class="muted">sin dependencias todavía</div>'; return; }

  // solo participan las tareas con alguna arista
  const inGraph = new Set();
  deps.forEach(d => { inGraph.add(d.task_id); inGraph.add(d.depends_on_id); });
  const nodes = state.tasks.filter(t => inGraph.has(t.id));

  // capa = camino más largo desde una raíz (orden topológico por niveles)
  const dmap = {};
  deps.forEach(d => (dmap[d.task_id] = dmap[d.task_id] || []).push(d.depends_on_id));
  const layerOf = {};
  const calc = (id, seen) => {
    if (layerOf[id] !== undefined) return layerOf[id];
    seen = seen || new Set();
    if (seen.has(id)) return 0;
    seen.add(id);
    const ds = dmap[id] || [];
    return (layerOf[id] = ds.length ? Math.max(...ds.map(x => calc(x, seen))) + 1 : 0);
  };
  nodes.forEach(n => calc(n.id));

  const byLayer = [];
  nodes.forEach(n => (byLayer[layerOf[n.id]] = byLayer[layerOf[n.id]] || []).push(n));

  const NW = 150, NH = 34, GX = 14, ROW = 88, PAD = 18;
  const maxRow = Math.max(...byLayer.map(r => (r ? r.length : 0)));
  const W = Math.max(maxRow * (NW + GX) + PAD * 2, 420);
  const H = byLayer.length * ROW + PAD;

  const pos = {};
  byLayer.forEach((row, l) => {
    if (!row) return;
    row.sort((a, b) => a.layer_id - b.layer_id || a.id - b.id);
    const total = row.length * (NW + GX) - GX;
    row.forEach((n, i) => { pos[n.id] = { x: (W - total) / 2 + i * (NW + GX), y: PAD + l * ROW }; });
  });

  const col = t => t.status === "done" ? "#3fb96b"
    : t.status === "in_progress" ? "#e0a83c"
    : isBlocked(t) ? "#e05c5c" : "#8a93a6";

  const critical = id => plan && plan.crit && plan.crit.has(id);
  let svg = "";
  for (const d of deps) {
    const a = pos[d.depends_on_id], b = pos[d.task_id];
    if (!a || !b) continue;
    const hot = critical(d.task_id) && critical(d.depends_on_id);
    const x1 = a.x + NW / 2, y1 = a.y + NH, x2 = b.x + NW / 2, y2 = b.y;
    svg += `<path d="M${x1},${y1} C${x1},${y1 + 36} ${x2},${y2 - 36} ${x2},${y2}" fill="none" stroke="${hot ? "#e05c5c" : "#2a3348"}" stroke-width="${hot ? 2.4 : 1.5}" marker-end="url(#arr)"/>`;
  }
  for (const n of nodes) {
    const p = pos[n.id], c = col(n);
    const label = n.title.length > 21 ? n.title.slice(0, 20) + "…" : n.title;
    svg += `<g><rect x="${p.x}" y="${p.y}" width="${NW}" height="${NH}" rx="8" fill="#1d2537" stroke="${c}" stroke-width="${critical(n.id) ? 3 : 1.6}"/>
      <circle cx="${p.x + 13}" cy="${p.y + NH / 2}" r="4" fill="${c}"/>
      <text x="${p.x + 24}" y="${p.y + NH / 2 + 4}" fill="#e8ecf4" font-size="11">${esc(label)}</text>
      <title>${esc(n.title)} — ${n.status}${isBlocked(n) ? " (bloqueada)" : ""}</title></g>`;
  }
  host.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">
    <defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2a3348"/></marker></defs>
    ${svg}</svg>`;
}

function render() {
  const { layers, tasks, decisions, events } = state;
  const plan = computeSchedule();

  // sincronizar selects de filtros
  const flt = getFilters();
  if ($("#fWho")) { $("#fWho").value = flt.who || ""; $("#fSt").value = flt.st || ""; }

  // global + pipeline
  const gp = pct(tasks);
  $("#globalFill").style.width = gp + "%";
  $("#globalLabel").textContent = `${gp} % · ${tasks.filter(t => t.status === "done").length}/${tasks.length} tareas`;

  const pipe = $("#pipeline");
  pipe.innerHTML = "";
  layers.forEach((l, i) => {
    const lt = tasks.filter(t => t.layer_id === l.id);
    const p = pct(lt);
    const chip = document.createElement("div");
    chip.className = "pipe-chip" + (lt.some(t => t.status === "in_progress") ? " active" : "");
    chip.innerHTML = `<span>${l.title.split("—")[0].trim()}</span><span class="pct">${p} %</span>`;
    pipe.appendChild(chip);
    if (i < layers.length - 1) {
      const a = document.createElement("span");
      a.className = "pipe-arrow"; a.textContent = "→";
      pipe.appendChild(a);
    }
  });

  // capas y tareas
  const cont = $("#layers");
  cont.innerHTML = "";
  for (const l of layers) {
    const lt = tasks.filter(t => t.layer_id === l.id);
    const sec = document.createElement("div");
    sec.className = "layer";
    sec.innerHTML = `
      <div class="layer-head"><h2>${esc(l.title)}</h2><span class="sub">${esc(l.subtitle)}</span></div>
      <div class="layer-bar"><div class="layer-fill" style="width:${pct(lt)}%"></div></div>`;
    // cabecera plegable con contador
    const head = sec.querySelector(".layer-head");
    const isCol = getCollapsed().has(l.id);
    const caret = document.createElement("span");
    caret.className = "caret"; caret.textContent = isCol ? "▸" : "▾";
    head.prepend(caret);
    const count = document.createElement("span");
    count.className = "layer-count";
    count.textContent = `${lt.filter(t => t.status === "done").length}/${lt.length}`;
    head.appendChild(count);
    head.style.cursor = "pointer";
    head.onclick = () => {
      const c = getCollapsed();
      c.has(l.id) ? c.delete(l.id) : c.add(l.id);
      localStorage.setItem("roadmap_collapsed", JSON.stringify([...c]));
      render();
    };

    if (!isCol) {
      // Raíces primero; bajo cada una, sus subtareas (1 nivel). Filtros activos.
      const ids = new Set(lt.map(t => t.id));
      const roots = lt.filter(t => !t.parent_id || !ids.has(t.parent_id));
      for (const t of roots) {
        const kids = lt.filter(x => x.parent_id === t.id);
        if (!taskMatches(t) && !kids.some(taskMatches)) continue;
        sec.appendChild(taskRow(t, false));
        for (const s of kids) if (taskMatches(s) || taskMatches(t)) sec.appendChild(taskRow(s, true));
      }
      const add = document.createElement("button");
      add.className = "add-task"; add.textContent = "+ añadir tarea";
      add.onclick = async () => {
        const title = prompt("Título de la nueva tarea:");
        if (title) await mutate("POST", "api/tasks", { layer_id: l.id, title });
      };
      sec.appendChild(add);
    }
    cont.appendChild(sec);
  }

  // decisiones
  const dv = $("#decisions");
  dv.innerHTML = "";
  for (const d of decisions) {
    const el = document.createElement("div");
    el.className = "decision";
    el.innerHTML = `
      <span class="dstatus ${d.status}" title="Clic para ciclar">${DSTATUS_LABEL[d.status] || d.status}</span>
      <span class="code">${esc(d.code)}</span><span>${esc(d.title)}</span>
      <div class="ddetail">${esc(d.detail)}</div>`;
    $(".dstatus", el).onclick = () => {
      const next = DSTATUS_CYCLE[(DSTATUS_CYCLE.indexOf(d.status) + 1) % DSTATUS_CYCLE.length];
      mutate("PATCH", `api/decisions/${d.id}`, { status: next });
    };
    dv.appendChild(el);
  }

  renderGantt(plan);
  renderDepGraph(plan);

  // historial
  const ev = $("#events");
  ev.innerHTML = "";
  for (const e of events) {
    const li = document.createElement("li");
    const d = new Date(e.ts * 1000);
    li.innerHTML = `<span class="actor">${esc(e.actor)}</span> ${esc(e.action)}
      <time>${d.toLocaleDateString("es-ES", { day: "2-digit", month: "short" })} ${d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })}</time>`;
    ev.appendChild(li);
  }
}

function taskRow(t, isSub) {
  const blocked = isBlocked(t);
  const row = document.createElement("div");
  row.className = "task " + t.status + (isSub ? " sub" : "") + (blocked ? " blocked" : "");

  const st = document.createElement("span");
  st.className = "status " + t.status;
  st.textContent = STATUS_LABEL[t.status] || t.status;
  st.title = blocked ? "Bloqueada: tiene dependencias sin completar" : "Clic para ciclar estado";
  st.onclick = () => {
    const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(t.status) + 1) % STATUS_CYCLE.length];
    if (next === "done" && blocked &&
        !confirm("⛓ Esta tarea tiene dependencias sin completar. ¿Marcarla como hecha igualmente?")) return;
    mutate("PATCH", `api/tasks/${t.id}`, { status: next });
  };

  const body = document.createElement("div");
  body.className = "task-body";
  const title = document.createElement("div");
  title.className = "task-title";
  if (blocked) {
    const lock = document.createElement("span");
    lock.className = "blocked-badge"; lock.textContent = "🔒 ";
    lock.title = "Bloqueada por dependencias";
    title.appendChild(lock);
  }
  title.appendChild(document.createTextNode(t.title));
  editable(title, v => mutate("PATCH", `api/tasks/${t.id}`, { title: v.replace(/^🔒\s*/, "") }));
  const detail = document.createElement("div");
  detail.className = "task-detail"; detail.textContent = t.detail;
  editable(detail, v => mutate("PATCH", `api/tasks/${t.id}`, { detail: v }));
  body.append(title, detail);

  // Chips de dependencias: «depende de» + botones para quitar/añadir.
  const depIds = depsOf(t.id);
  const depRow = document.createElement("div");
  depRow.className = "dep-row";
  if (depIds.length) {
    const lbl = document.createElement("span");
    lbl.className = "dep-label"; lbl.textContent = "⛓ depende de:";
    depRow.appendChild(lbl);
    for (const id of depIds) {
      const d = taskById(id);
      const chip = document.createElement("span");
      chip.className = "dep-chip" + (d && d.status === "done" ? " ok" : "");
      chip.textContent = d ? d.title.slice(0, 32) : `#${id}`;
      chip.title = "Clic para eliminar esta dependencia";
      chip.onclick = () => mutate("DELETE", `api/tasks/${t.id}/deps/${id}`);
      depRow.appendChild(chip);
    }
  }
  const addDep = document.createElement("button");
  addDep.className = "dep-add"; addDep.textContent = depIds.length ? "+" : "+ dep";
  addDep.title = "Añadir dependencia";
  addDep.onclick = () => {
    const id = pickTask(t.id);
    if (id) mutate("POST", `api/tasks/${t.id}/deps`, { depends_on_id: id });
  };
  depRow.appendChild(addDep);
  body.appendChild(depRow);

  const asg = document.createElement("span");
  asg.className = "assignee" + (t.assignee ? "" : " empty");
  asg.textContent = t.assignee || "sin asignar";
  asg.title = "Clic para asignar";
  asg.onclick = () => {
    const v = prompt("Asignar a:", t.assignee || getName());
    if (v !== null) mutate("PATCH", `api/tasks/${t.id}`, { assignee: v.trim() });
  };

  const del = document.createElement("button");
  del.className = "del"; del.textContent = "✕"; del.title = "Eliminar tarea";
  del.onclick = () => {
    if (confirm(`¿Eliminar «${t.title}»?`)) mutate("DELETE", `api/tasks/${t.id}`);
  };

  // estimación / fechas fijas (alimenta el Gantt)
  const est = document.createElement("span");
  est.className = "est-chip";
  est.textContent = `~${t.estimate_days || 1}d${t.start_date || t.due_date ? " 📌" : ""}`;
  est.title = "Estimación y fechas (clic para editar)";
  est.onclick = () => {
    const v = prompt(
      "Estimación:\n  2                      → 2 días\n  2 2026-07-10           → 2 días, no antes del 10-jul\n  2026-07-10..2026-07-12 → rango fijo\n  x                      → quitar fechas fijas",
      t.estimate_days || 1);
    if (v == null) return;
    const s = String(v).trim();
    if (s === "x") return mutate("PATCH", `api/tasks/${t.id}`, { start_date: null, due_date: null });
    const range = s.match(/^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$/);
    if (range) return mutate("PATCH", `api/tasks/${t.id}`, { start_date: range[1], due_date: range[2] });
    const m = s.match(/^([\d.]+)(?:\s+(\d{4}-\d{2}-\d{2}))?$/);
    if (m) return mutate("PATCH", `api/tasks/${t.id}`, { estimate_days: parseFloat(m[1]), start_date: m[2] || null });
    toast("Formato no reconocido", true);
  };

  row.append(st, body, est, asg);
  if (!isSub) {
    const sub = document.createElement("button");
    sub.className = "add-sub"; sub.textContent = "+sub"; sub.title = "Añadir subtarea";
    sub.onclick = async () => {
      const title = prompt(`Subtarea de «${t.title.slice(0, 40)}»:`);
      if (title) await mutate("POST", "api/tasks", { layer_id: t.layer_id, title, parent_id: t.id });
    };
    row.append(sub);
  }
  row.append(del);
  return row;
}

/* doble clic → edición inline; Enter o blur → guardar */
function editable(el, save) {
  el.addEventListener("dblclick", () => {
    el.contentEditable = "true";
    el.focus();
    document.getSelection().selectAllChildren(el);
    const done = () => {
      el.contentEditable = "false";
      const v = el.textContent.trim();
      save(v);
    };
    el.addEventListener("blur", done, { once: true });
    el.addEventListener("keydown", e => {
      if (e.key === "Enter") { e.preventDefault(); el.blur(); }
      if (e.key === "Escape") { el.removeEventListener("blur", done); el.contentEditable = "false"; load(); }
    });
  });
}

/* ---------- util ---------- */
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
let toastTimer;
function toast(msg, err = false) {
  let el = $(".toast");
  if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); }
  el.textContent = msg;
  el.classList.toggle("err", err);
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
}

/* ---------- init ---------- */
renderWho();
load();
setInterval(load, 20000);   // refresco: ver cambios del otro
