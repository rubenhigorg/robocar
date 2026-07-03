# Roadmap web del TFM

Web autoalojada para seguir el estado del roadmap del TFM entre varias personas.
Estado compartido y persistente (SQLite en el servidor), con historial de quién marcó qué.

- **Lectura:** libre para cualquiera con la URL.
- **Escritura:** requiere la clave (`ROADMAP_KEY`), que cada uno introduce una vez (botón 🔑).
- **Semilla:** la base de datos se crea sola al primer arranque con el estado real del roadmap.

## Desplegar (Docker)

```bash
cd tools/roadmap-web
ROADMAP_KEY=una-clave-vuestra docker compose up -d --build
```

Web en `http://<servidor>:8090`. El estado vive en `./data/roadmap.db` (volumen), así que
sobrevive a rebuilds. Para resembrar desde cero: parar, borrar `data/`, arrancar.

## Uso

| Acción | Cómo |
|---|---|
| Cambiar estado de una tarea | Clic en el chip (Pendiente → En curso → Hecho) |
| Editar título/descripción | Doble clic en el texto · Enter/blur guarda · Esc cancela |
| Asignar tarea | Clic en el chip de asignado |
| Añadir / eliminar tarea | Botón «+ añadir tarea» / ✕ |
| Ciclar una decisión | Clic en su chip de estado |

## API (para automatizar — p. ej. Claude desde las sesiones)

```bash
# leer todo el estado
curl -s http://<servidor>:8090/api/state | jq

# marcar la tarea 2 como hecha
curl -s -X PATCH http://<servidor>:8090/api/tasks/2 \
  -H "Authorization: Bearer $ROADMAP_KEY" -H "X-Actor: Claude" \
  -H "Content-Type: application/json" -d '{"status":"done"}'

# crear una tarea en la capa 1
curl -s -X POST http://<servidor>:8090/api/tasks \
  -H "Authorization: Bearer $ROADMAP_KEY" -H "X-Actor: Claude" \
  -H "Content-Type: application/json" \
  -d '{"layer_id":1,"title":"Nueva tarea","detail":"..."}'
```

Endpoints: `GET /api/state` · `POST /api/tasks` · `PATCH|DELETE /api/tasks/{id}` ·
`PATCH /api/decisions/{id}` · `PATCH /api/layers/{id}` · `GET /api/health`.

## Sin Docker (desarrollo)

```bash
pip install fastapi "uvicorn[standard]"
ROADMAP_KEY=loquesea uvicorn app:app --port 8090
```
