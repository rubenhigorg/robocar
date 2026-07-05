"""Roadmap web del TFM Robocar.

Un solo proceso: API REST (FastAPI) + frontend estático + SQLite.
Lectura libre; mutaciones requieren `Authorization: Bearer $ROADMAP_KEY`.
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

DB_PATH = os.environ.get("ROADMAP_DB", os.path.join(os.path.dirname(__file__), "data", "roadmap.db"))
AUTH_KEY = os.environ.get("ROADMAP_KEY", "robocar")

app = FastAPI(title="Robocar TFM Roadmap", docs_url=None, redoc_url=None)


@app.middleware("http")
async def cache_headers(request: Request, call_next):
    # El HTML nunca se cachea (referencia css/js con ?v=N para bustear al desplegar).
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@contextmanager
def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS layers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subtitle TEXT DEFAULT '',
                position INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                detail TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',      -- pending | in_progress | done
                assignee TEXT DEFAULT '',
                position INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS decisions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,                 -- D1, D2...
                title TEXT NOT NULL,
                status TEXT DEFAULT 'open',         -- open | planned | closed
                detail TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                actor TEXT DEFAULT '',
                action TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_deps(
                task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                depends_on_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, depends_on_id)
            );
            """
        )
        # Migraciones no destructivas sobre BDs existentes.
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(tasks)")]
        if "parent_id" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN parent_id INTEGER REFERENCES tasks(id)")
        if "estimate_days" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN estimate_days REAL DEFAULT 1.0")
            conn.execute("ALTER TABLE tasks ADD COLUMN start_date TEXT")   # fija manual (opcional)
            conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")     # fija manual (opcional)
            conn.execute("ALTER TABLE tasks ADD COLUMN done_at INTEGER")   # epoch al completarse
        if conn.execute("SELECT COUNT(*) c FROM layers").fetchone()["c"] == 0:
            seed(conn)


def seed(conn):
    """Estado real del roadmap a fecha de la creación (jul 2026)."""
    layers = [
        ("Capa 0 — Fundamentos ROS2", "TF · odometría · puente Ackermann (el riesgo principal)"),
        ("Capa 1 — Percepción / SLAM", "RPLidar C1 + Cartographer → OE1: localización < 10 cm"),
        ("Capa 2 — Navegación", "Nav2 + TEB → OE2: éxito > 90 %"),
        ("Capa 3 — Interfaz natural", "MCP Server + LLM → OE3/OE4: interpretación > 85 %"),
        ("Capa 4 — Validación y cierre", "Batería end-to-end · métricas · Cap. 4-5 de la memoria"),
    ]
    for i, (t, s) in enumerate(layers):
        conn.execute("INSERT INTO layers(title, subtitle, position) VALUES(?,?,?)", (t, s, i))

    tasks = [
        # (layer 1-based, title, detail, status, assignee)
        (1, "0.1 Migrar a ROS2 Humble", "Instalado ros-base+joy, workspace recompilado, Iron purgado, clave GPG de ROS renovada.", "done", "Claude"),
        (1, "0.2 Puente /cmd_vel → PCA9685", "Código escrito y compilado en la Pi; lógica validada (barrido dirección). Falta: confirmar sentido de giro, probar tracción suave, commitear.", "in_progress", "Rubén+Claude"),
        (1, "0.3 URDF + árbol TF", "base_link, laser (offset montaje), imu_link, ruedas; robot_state_publisher. Puerta de la Capa 1.", "pending", ""),
        (1, "0.4 Odometría (D2=A)", "Scan-matching de Cartographer como fuente de pose; sin odom de ruedas inicialmente.", "pending", ""),
        (1, "0.5 Sanear /imu", "Añadir header (timestamp+frame_id) y covarianzas a accelerometer_node. Crítico solo si D2→B.", "pending", ""),
        (1, "Odometría encoder+IMU (plan B / mejora)", "Nodo modelo-bicicleta con el sensor de rueda nuevo + yaw IMU. Paralelizable; mejora Cartographer aunque sigamos en A.", "pending", "Rubén"),
        (2, "rplidar_ros publicando /scan", "Integrar el RPLidar C1 en ROS2 (ya validado fuera de ROS2 en pruebas/rplidar).", "pending", ""),
        (2, "Configurar Cartographer 2D", "Config .lua ajustada a Raspberry Pi (resolución/optimización contenidas).", "pending", ""),
        (2, "Construir y guardar el mapa", "Teleoperar con el mando y guardar .pgm + .yaml del entorno de prueba.", "pending", ""),
        (2, "Base de datos SQLite de lugares", "≥3 lugares semánticos (nombre → coordenada). Valida OE1 junto a localización <10 cm.", "pending", ""),
        (3, "Configurar stack Nav2", "BT Navigator, planner global, costmaps (static+inflation+obstacle), AMCL.", "pending", ""),
        (3, "Controlador local Ackermann (TEB)", "Decisión D3: TEB / RPP / MPPI, no DWB diferencial. Incluye conversión Ackermann fiel (δ=atan(L·ω/v)).", "pending", ""),
        (3, "Servicio de resolución semántica", "nombre de lugar → PoseStamped leyendo la SQLite.", "pending", ""),
        (3, "Validar navegación punto a punto", "≥20 ensayos, destino a <20 cm, éxito >90 % (OE2).", "pending", ""),
        (4, "MCP Server (FastMCP) + 4 tools", "navigate_to, get_current_location, list_known_places, stop_navigation. Paralelizable YA contra Nav2 mock.", "pending", ""),
        (4, "Cliente de acción rclpy → NavigateToPose", "Meta, feedback, éxito/fallo/cancelación.", "pending", ""),
        (4, "Host conversacional + Claude API", "System prompt del asistente de navegación + bucle tool use.", "pending", ""),
        (5, "Batería de pruebas end-to-end", "Comandos simples, secuencias compuestas, casos de error (≥20 comandos, >85 % OE4).", "pending", ""),
        (5, "Métricas OE1-OE4 + latencia", "RMSE localización, éxito nav, interpretación, latencia mediana <5 s.", "pending", ""),
        (5, "Redacción Cap. 4 y 5 + Resumen/Abstract", "Entregas 2 y 3 de la memoria.", "pending", "Rubén"),
    ]
    for i, (lid, t, d, st, a) in enumerate(tasks):
        conn.execute(
            "INSERT INTO tasks(layer_id, title, detail, status, assignee, position) VALUES(?,?,?,?,?,?)",
            (lid, t, d, st, a, i),
        )

    decisions = [
        ("D1", "Distro ROS2 → Humble", "closed", "Migrada la Pi (jul 2026). LTS hasta 2027, alineada con la memoria."),
        ("D2", "Odometría → opción A (scan-matching)", "closed", "Cartographer estima la pose. Plan B (encoder+IMU+EKF) si no se cumple OE1; habilitado por el sensor de rueda."),
        ("D3", "Controlador local → TEB", "planned", "Por cinemática Ackermann. Se cierra al configurar Nav2 (Capa 2)."),
        ("D4", "Puente de actuación → extender car_control_node", "planned", "Un único dueño del bus I2C. Implementándose en el hito 0.2."),
    ]
    for c, t, st, d in decisions:
        conn.execute("INSERT INTO decisions(code, title, status, detail) VALUES(?,?,?,?)", (c, t, st, d))

    conn.execute(
        "INSERT INTO events(ts, actor, action) VALUES(?,?,?)",
        (int(time.time()), "Claude", "Roadmap creado con el estado inicial (0.1 hecho, 0.2 en curso)"),
    )


def require_key(authorization: Optional[str]):
    if authorization != f"Bearer {AUTH_KEY}":
        raise HTTPException(status_code=401, detail="Clave incorrecta o ausente")


def log_event(conn, actor: str, action: str):
    conn.execute("INSERT INTO events(ts, actor, action) VALUES(?,?,?)", (int(time.time()), actor or "?", action))


@app.get("/api/state")
def get_state():
    with db() as conn:
        return {
            "layers": [dict(r) for r in conn.execute("SELECT * FROM layers ORDER BY position, id")],
            "tasks": [dict(r) for r in conn.execute("SELECT * FROM tasks ORDER BY position, id")],
            "decisions": [dict(r) for r in conn.execute("SELECT * FROM decisions ORDER BY code")],
            "events": [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 40")],
            "deps": [dict(r) for r in conn.execute("SELECT * FROM task_deps")],
        }


def creates_cycle(conn, task_id: int, depends_on_id: int) -> bool:
    """¿Añadir task_id→depends_on_id crearía un ciclo? DFS sobre las deps existentes."""
    stack, seen = [depends_on_id], set()
    while stack:
        cur = stack.pop()
        if cur == task_id:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(r["depends_on_id"] for r in conn.execute(
            "SELECT depends_on_id FROM task_deps WHERE task_id=?", (cur,)))
    return False


@app.post("/api/tasks/{task_id}/deps")
async def add_dep(task_id: int, request: Request,
                  authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    require_key(authorization)
    dep_id = int((await request.json()).get("depends_on_id", 0))
    if dep_id == task_id:
        raise HTTPException(status_code=400, detail="Una tarea no puede depender de sí misma")
    with db() as conn:
        t = conn.execute("SELECT title FROM tasks WHERE id=?", (task_id,)).fetchone()
        d = conn.execute("SELECT title FROM tasks WHERE id=?", (dep_id,)).fetchone()
        if not t or not d:
            raise HTTPException(status_code=404, detail="Tarea inexistente")
        if creates_cycle(conn, task_id, dep_id):
            raise HTTPException(status_code=409, detail="Crearía un ciclo de dependencias")
        conn.execute("INSERT OR IGNORE INTO task_deps(task_id, depends_on_id) VALUES(?,?)",
                     (task_id, dep_id))
        log_event(conn, x_actor, f"Dependencia: «{t['title']}» ahora depende de «{d['title']}»")
    return {"ok": True}


@app.delete("/api/tasks/{task_id}/deps/{dep_id}")
def remove_dep(task_id: int, dep_id: int,
               authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    require_key(authorization)
    with db() as conn:
        conn.execute("DELETE FROM task_deps WHERE task_id=? AND depends_on_id=?", (task_id, dep_id))
        t = conn.execute("SELECT title FROM tasks WHERE id=?", (task_id,)).fetchone()
        log_event(conn, x_actor, f"Dependencia eliminada de «{t['title'] if t else task_id}»")
    return {"ok": True}


TASK_FIELDS = {"title", "detail", "status", "assignee", "position", "layer_id", "parent_id",
               "estimate_days", "start_date", "due_date", "done_at"}
DECISION_FIELDS = {"code", "title", "status", "detail"}
LAYER_FIELDS = {"title", "subtitle", "position"}


async def patch_row(request: Request, table: str, row_id: int, allowed: set,
                    authorization: Optional[str], actor: str, label: str):
    require_key(authorization)
    body = {k: v for k, v in (await request.json()).items() if k in allowed}
    if not body:
        raise HTTPException(status_code=400, detail="Sin campos válidos")
    with db() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No existe")
        # Al completar una tarea se sella done_at (y se limpia si se reabre).
        if table == "tasks" and "status" in body:
            body = dict(body, done_at=int(time.time()) if body["status"] == "done" else None)
        sets = ", ".join(f"{k}=?" for k in body)
        conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", (*body.values(), row_id))
        if "status" in body:
            log_event(conn, actor, f"{label} «{row['title']}» → {body['status']}")
        else:
            log_event(conn, actor, f"{label} «{row['title']}» editado")
    return {"ok": True}


@app.patch("/api/tasks/{task_id}")
async def patch_task(task_id: int, request: Request,
                     authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    return await patch_row(request, "tasks", task_id, TASK_FIELDS, authorization, x_actor, "Tarea")


@app.patch("/api/decisions/{decision_id}")
async def patch_decision(decision_id: int, request: Request,
                         authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    return await patch_row(request, "decisions", decision_id, DECISION_FIELDS, authorization, x_actor, "Decisión")


@app.patch("/api/layers/{layer_id}")
async def patch_layer(layer_id: int, request: Request,
                      authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    return await patch_row(request, "layers", layer_id, LAYER_FIELDS, authorization, x_actor, "Capa")


@app.post("/api/tasks")
async def create_task(request: Request,
                      authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    require_key(authorization)
    body = await request.json()
    if not body.get("title") or not body.get("layer_id"):
        raise HTTPException(status_code=400, detail="title y layer_id son obligatorios")
    with db() as conn:
        pos = conn.execute("SELECT COALESCE(MAX(position),0)+1 p FROM tasks WHERE layer_id=?",
                           (body["layer_id"],)).fetchone()["p"]
        parent_id = body.get("parent_id")
        cur = conn.execute(
            "INSERT INTO tasks(layer_id, title, detail, status, assignee, position, parent_id)"
            " VALUES(?,?,?,?,?,?,?)",
            (body["layer_id"], body["title"], body.get("detail", ""),
             body.get("status", "pending"), body.get("assignee", ""), pos, parent_id),
        )
        kind = "Subtarea" if parent_id else "Tarea"
        log_event(conn, x_actor, f"{kind} «{body['title']}» creada")
        return {"ok": True, "id": cur.lastrowid}


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int,
                authorization: Optional[str] = Header(None), x_actor: str = Header("")):
    require_key(authorization)
    with db() as conn:
        row = conn.execute("SELECT title FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No existe")
        # Las subtareas huérfanas suben a nivel raíz (no se borran en cascada).
        conn.execute("UPDATE tasks SET parent_id=NULL WHERE parent_id=?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        log_event(conn, x_actor, f"Tarea «{row['title']}» eliminada")
    return {"ok": True}


@app.get("/api/health")
def health():
    return {"ok": True}


init_db()
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")
