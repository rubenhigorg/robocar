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

function render() {
  const { layers, tasks, decisions, events } = state;

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
    // Raíces primero; bajo cada una, sus subtareas (1 nivel).
    const ids = new Set(lt.map(t => t.id));
    const roots = lt.filter(t => !t.parent_id || !ids.has(t.parent_id));
    for (const t of roots) {
      sec.appendChild(taskRow(t, false));
      for (const s of lt.filter(x => x.parent_id === t.id)) sec.appendChild(taskRow(s, true));
    }
    const add = document.createElement("button");
    add.className = "add-task"; add.textContent = "+ añadir tarea";
    add.onclick = async () => {
      const title = prompt("Título de la nueva tarea:");
      if (title) await mutate("POST", "api/tasks", { layer_id: l.id, title });
    };
    sec.appendChild(add);
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

  row.append(st, body, asg);
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
