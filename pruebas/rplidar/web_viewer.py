import argparse
import json
import queue
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SERIAL = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 460800
DEFAULT_MAX_DISTANCE = 12000
SERIAL_PORT = DEFAULT_SERIAL
BAUDRATE = DEFAULT_BAUDRATE
MAX_DISTANCE = DEFAULT_MAX_DISTANCE
STREAM = None


def build_stream_command():
    return [
        str(BASE_DIR / "rplidar_stream"),
        "--serial",
        SERIAL_PORT,
        "--baudrate",
        str(BAUDRATE),
        "--max-distance",
        str(MAX_DISTANCE),
    ]


def index():
    return f"""
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RPLIDAR C1 Viewer</title>
    <style>
        :root {{
            --bg: #101412;
            --panel: #e7ece8;
            --ink: #15201a;
            --muted: #607168;
            --accent: #2bd67b;
            --warn: #d68b2b;
            --grid: rgba(231, 236, 232, 0.12);
        }}

        * {{ box-sizing: border-box; }}

        body {{
            margin: 0;
            min-height: 100vh;
            color: var(--panel);
            background:
                radial-gradient(circle at 20% 10%, rgba(43, 214, 123, 0.12), transparent 28rem),
                linear-gradient(135deg, #101412 0%, #18231d 55%, #0d1110 100%);
            font-family: "Aptos", "Segoe UI", sans-serif;
        }}

        main {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) 22rem;
            gap: 1rem;
            min-height: 100vh;
            padding: 1rem;
        }}

        .scan-area {{
            position: relative;
            min-height: calc(100vh - 2rem);
            border: 1px solid rgba(231, 236, 232, 0.16);
            background: rgba(10, 15, 13, 0.72);
            overflow: hidden;
        }}

        canvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}

        aside {{
            color: var(--ink);
            background: var(--panel);
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        h1 {{
            margin: 0;
            font-size: 1.35rem;
            letter-spacing: 0;
        }}

        .metric {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 0.5rem;
            border-top: 1px solid rgba(21, 32, 26, 0.16);
            padding-top: 0.75rem;
        }}

        .label {{
            color: var(--muted);
            font-size: 0.85rem;
        }}

        .value {{
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .controls {{
            display: grid;
            gap: 0.75rem;
        }}

        label {{
            display: grid;
            gap: 0.35rem;
            color: var(--muted);
            font-size: 0.85rem;
        }}

        input[type="range"] {{
            width: 100%;
        }}

        .status {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--muted);
        }}

        .dot {{
            width: 0.65rem;
            height: 0.65rem;
            background: var(--warn);
            border-radius: 50%;
        }}

        .dot.live {{
            background: var(--accent);
            box-shadow: 0 0 1rem rgba(43, 214, 123, 0.8);
        }}

        pre {{
            overflow: auto;
            max-height: 12rem;
            margin: 0;
            padding: 0.75rem;
            background: rgba(21, 32, 26, 0.08);
            color: var(--ink);
            font-size: 0.78rem;
        }}

        @media (max-width: 900px) {{
            main {{
                grid-template-columns: 1fr;
            }}

            .scan-area {{
                min-height: 68vh;
            }}
        }}
    </style>
</head>
<body>
    <main>
        <section class="scan-area">
            <canvas id="scan"></canvas>
        </section>
        <aside>
            <div>
                <h1>RPLIDAR C1</h1>
                <div class="status"><span id="dot" class="dot"></span><span id="status">conectando</span></div>
            </div>

            <div class="metric"><span class="label">Puerto</span><span class="value">{SERIAL_PORT}</span></div>
            <div class="metric"><span class="label">Baudrate</span><span class="value">{BAUDRATE}</span></div>
            <div class="metric"><span class="label">Puntos</span><span id="points" class="value">0</span></div>
            <div class="metric"><span class="label">FPS</span><span id="fps" class="value">0.0</span></div>
            <div class="metric"><span class="label">Distancia max</span><span id="rangeLabel" class="value">6000 mm</span></div>

            <div class="controls">
                <label>
                    Rango visible
                    <input id="range" type="range" min="1000" max="12000" step="500" value="6000">
                </label>
                <label>
                    <span><input id="fade" type="checkbox" checked> Estela</span>
                </label>
            </div>

            <pre id="meta">Esperando datos del SDK...</pre>
        </aside>
    </main>

    <script>
        const canvas = document.getElementById("scan");
        const ctx = canvas.getContext("2d");
        const rangeInput = document.getElementById("range");
        const rangeLabel = document.getElementById("rangeLabel");
        const pointsEl = document.getElementById("points");
        const fpsEl = document.getElementById("fps");
        const metaEl = document.getElementById("meta");
        const statusEl = document.getElementById("status");
        const dotEl = document.getElementById("dot");
        const fadeEl = document.getElementById("fade");

        let points = [];
        let lastFrameAt = performance.now();
        let maxRange = Number(rangeInput.value);
        let metadata = {{}};

        function resize() {{
            const rect = canvas.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.floor(rect.width * dpr);
            canvas.height = Math.floor(rect.height * dpr);
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            draw();
        }}

        function drawGrid(cx, cy, radius) {{
            ctx.strokeStyle = "rgba(231, 236, 232, 0.12)";
            ctx.lineWidth = 1;
            for (let i = 1; i <= 4; i++) {{
                ctx.beginPath();
                ctx.arc(cx, cy, radius * i / 4, 0, Math.PI * 2);
                ctx.stroke();
            }}
            for (let deg = 0; deg < 360; deg += 30) {{
                const a = (deg - 90) * Math.PI / 180;
                ctx.beginPath();
                ctx.moveTo(cx, cy);
                ctx.lineTo(cx + Math.cos(a) * radius, cy + Math.sin(a) * radius);
                ctx.stroke();
            }}
        }}

        function draw() {{
            const width = canvas.clientWidth;
            const height = canvas.clientHeight;
            const cx = width / 2;
            const cy = height / 2;
            const radius = Math.min(width, height) * 0.45;

            if (fadeEl.checked) {{
                ctx.fillStyle = "rgba(16, 20, 18, 0.28)";
                ctx.fillRect(0, 0, width, height);
            }} else {{
                ctx.clearRect(0, 0, width, height);
                ctx.fillStyle = "#101412";
                ctx.fillRect(0, 0, width, height);
            }}

            drawGrid(cx, cy, radius);

            ctx.fillStyle = "#2bd67b";
            for (const point of points) {{
                const angle = (point[0] - 90) * Math.PI / 180;
                const distance = Math.min(point[1], maxRange);
                const r = distance / maxRange * radius;
                const q = Math.max(0.25, Math.min(1, point[2] / 63));
                ctx.globalAlpha = q;
                ctx.beginPath();
                ctx.arc(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r, 2.1, 0, Math.PI * 2);
                ctx.fill();
            }}
            ctx.globalAlpha = 1;

            ctx.fillStyle = "#e7ece8";
            ctx.beginPath();
            ctx.arc(cx, cy, 4, 0, Math.PI * 2);
            ctx.fill();
        }}

        rangeInput.addEventListener("input", () => {{
            maxRange = Number(rangeInput.value);
            rangeLabel.textContent = `${{maxRange}} mm`;
            draw();
        }});

        window.addEventListener("resize", resize);
        resize();

        const source = new EventSource("/events");
        source.onopen = () => {{
            statusEl.textContent = "recibiendo";
            dotEl.classList.add("live");
        }};
        source.onerror = () => {{
            statusEl.textContent = "sin datos";
            dotEl.classList.remove("live");
        }};
        source.onmessage = (event) => {{
            const message = JSON.parse(event.data);
            if (message.type === "scan") {{
                const now = performance.now();
                const fps = 1000 / Math.max(1, now - lastFrameAt);
                lastFrameAt = now;
                points = message.points;
                pointsEl.textContent = points.length;
                fpsEl.textContent = fps.toFixed(1);
                draw();
            }} else {{
                metadata[message.type] = message;
                metaEl.textContent = JSON.stringify(metadata, null, 2);
            }}
        }};
    </script>
</body>
</html>
"""


class LidarStream:
    def __init__(self):
        self.lock = threading.Lock()
        self.subscribers = set()
        self.process = None
        self.thread = None
        self.last_messages = []

    def subscribe(self):
        subscriber = queue.Queue(maxsize=4)
        with self.lock:
            for message in self.last_messages:
                subscriber.put_nowait(message)
            self.subscribers.add(subscriber)
            if self.process is None or self.process.poll() is not None:
                self._start_locked()
        return subscriber

    def unsubscribe(self, subscriber):
        with self.lock:
            self.subscribers.discard(subscriber)

    def _start_locked(self):
        self.process = subprocess.Popen(
            build_stream_command(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        process = self.process
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    message = line
                except json.JSONDecodeError:
                    message = json.dumps({"type": "log", "message": line})
                self._publish(message)
        finally:
            with self.lock:
                if self.process is process:
                    self.process = None
                code = process.poll()
                if code is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                self._publish_locked(json.dumps({"type": "log", "message": "stream finalizado"}))

    def _publish(self, message):
        with self.lock:
            self._publish_locked(message)

    def _publish_locked(self, message):
        parsed = json.loads(message)
        if parsed.get("type") != "scan":
            self.last_messages.append(message)
            self.last_messages = self.last_messages[-5:]
        dead = []
        for subscriber in self.subscribers:
            try:
                if subscriber.full():
                    subscriber.get_nowait()
                subscriber.put_nowait(message)
            except queue.Full:
                dead.append(subscriber)
        for subscriber in dead:
            self.subscribers.discard(subscriber)

    def stop(self):
        with self.lock:
            process = self.process
            self.process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()


def event_lines():
    subscriber = STREAM.subscribe()
    try:
        while True:
            try:
                message = subscriber.get(timeout=15)
            except queue.Empty:
                message = json.dumps({"type": "heartbeat", "time": time.time()})
            yield f"data: {message}\n\n".encode("utf-8")
    finally:
        STREAM.unsubscribe(subscriber)


class ViewerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            body = index().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if route == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                for payload in event_lines():
                    self.wfile.write(payload)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        self.send_error(404)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", default=DEFAULT_SERIAL)
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument("--max-distance", type=int, default=DEFAULT_MAX_DISTANCE)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    SERIAL_PORT = args.serial
    BAUDRATE = args.baudrate
    MAX_DISTANCE = args.max_distance
    STREAM = LidarStream()

    server = ThreadingHTTPServer((args.host, args.port), ViewerHandler)
    print(f"RPLIDAR web viewer: http://{args.host}:{args.port}")
    print(f"Serial: {args.serial} @ {args.baudrate}")
    try:
        server.serve_forever()
    finally:
        STREAM.stop()
