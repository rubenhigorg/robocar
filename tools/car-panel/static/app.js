/* Panel del Robocar — cliente rosbridge en vanilla JS, sin dependencias.
   Habla el protocolo JSON de rosbridge directamente por WebSocket. */

/* ── geometría real del coche (espejo del URDF, en metros) ── */
const CAR = {
  wheelbase: 0.175, track: 0.14, wheelR: 0.0325, wheelW: 0.026,
  chasL: 0.35, chasW: 0.175, rearOverhang: 0.085,
  laser: { x: 0.07 },
  us: [ { x: 0.24, y: 0.0525 }, { x: 0.25, y: 0 }, { x: 0.24, y: -0.0525 } ], // izq, centro, der
};

const TOPICS = [
  { name: "/imu",             type: "sensor_msgs/msg/Imu",     throttle: 100 },
  { name: "/ultrasound_data", type: "messages_pkg/msg/Distance", throttle: 200 },
  { name: "/energy",          type: "messages_pkg/msg/Energy", throttle: 1000 },
  { name: "/scan",            type: "sensor_msgs/msg/LaserScan", throttle: 200 },
];

const $ = s => document.querySelector(s);
const state = {
  imu: null, us: null, energy: null, scan: null,
  last: {},              // topic -> timestamp ms
  acc: [], gyro: [],     // buffers sparkline
  radius: 1.5,           // metros visibles desde el centro
};

/* ── conexión rosbridge ── */
const HOST = location.hostname || "robocar.local";
$("#host").textContent = HOST;
let ws = null;

function connect() {
  ws = new WebSocket(`ws://${HOST}:9090`);
  ws.onopen = () => {
    setConn("green", "conectado");
    for (const t of TOPICS) {
      ws.send(JSON.stringify({ op: "subscribe", topic: t.name, type: t.type, throttle_rate: t.throttle }));
    }
  };
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.op !== "publish") return;
    state.last[m.topic] = Date.now();
    if (m.topic === "/imu") onImu(m.msg);
    else if (m.topic === "/ultrasound_data") state.us = m.msg;
    else if (m.topic === "/energy") state.energy = m.msg;
    else if (m.topic === "/scan") state.scan = m.msg;
  };
  ws.onclose = () => { setConn("red", "sin conexión — reintentando…"); setTimeout(connect, 3000); };
  ws.onerror = () => ws.close();
}
function setConn(cls, txt) {
  $("#connDot").className = "dot " + cls;
  $("#connText").textContent = txt;
}

function onImu(msg) {
  state.imu = msg;
  const a = msg.linear_acceleration, g = msg.angular_velocity;
  state.acc.push([a.x, a.y, a.z]);  if (state.acc.length > 150) state.acc.shift();
  state.gyro.push([g.x, g.y, g.z]); if (state.gyro.length > 150) state.gyro.shift();
}

/* ── vista cenital (canvas) ── */
const view = $("#view"), vc = view.getContext("2d");

function carToScreen(x, y) {
  // coche: x adelante, y izquierda → pantalla: adelante = arriba
  const S = (view.width / 2) / state.radius;
  return [view.width / 2 - y * S, view.height / 2 - x * S];
}

function drawView() {
  const W = view.width, H = view.height, S = (W / 2) / state.radius;
  vc.clearRect(0, 0, W, H);

  // anillos de distancia cada 0.5 m
  vc.strokeStyle = "#1c2333"; vc.fillStyle = "#3a445c"; vc.font = "11px system-ui";
  for (let r = 0.5; r <= state.radius + 0.01; r += 0.5) {
    vc.beginPath(); vc.arc(W / 2, H / 2, r * S, 0, 2 * Math.PI); vc.stroke();
    vc.fillText(r.toFixed(1) + " m", W / 2 + 4, H / 2 - r * S + 12);
  }

  // puntos LIDAR
  if (state.scan) {
    const sc = state.scan;
    vc.fillStyle = "#ff5252";
    for (let i = 0; i < sc.ranges.length; i++) {
      const r = sc.ranges[i];
      if (!isFinite(r) || r < sc.range_min || r > sc.range_max) continue;
      const a = sc.angle_min + i * sc.angle_increment;
      const px = CAR.laser.x + r * Math.cos(a), py = r * Math.sin(a);
      const [sx, sy] = carToScreen(px, py);
      if (sx < 0 || sy < 0 || sx > W || sy > H) continue;
      vc.fillRect(sx - 1.5, sy - 1.5, 3, 3);
    }
    $("#scanInfo").textContent = `${sc.ranges.length} pts/vuelta`;
  }

  // haces de ultrasonidos (valores en cm → m)
  if (state.us) {
    const d = [state.us.left_distance, state.us.center_distance, state.us.right_distance];
    vc.fillStyle = "rgba(56,200,255,0.18)"; vc.strokeStyle = "#38c8ff";
    for (let i = 0; i < 3; i++) {
      const dist = Math.min(d[i] / 100, 4);
      if (!(dist > 0)) continue;
      const o = CAR.us[i], spread = 0.13; // ±~7.5º del HC-SR04
      vc.beginPath();
      const [ox, oy] = carToScreen(o.x, o.y);
      vc.moveTo(ox, oy);
      const [e1x, e1y] = carToScreen(o.x + dist * Math.cos(spread), o.y + dist * Math.sin(spread));
      const [e2x, e2y] = carToScreen(o.x + dist * Math.cos(-spread), o.y + dist * Math.sin(-spread));
      vc.lineTo(e1x, e1y); vc.lineTo(e2x, e2y); vc.closePath();
      vc.fill(); vc.stroke();
    }
  }

  drawCar(S);
}

function drawCar(S) {
  const rect = (x, y, w, h, color) => {   // (x,y)=centro en frame coche; w=largo(x), h=ancho(y)
    const [sx, sy] = carToScreen(x, y);
    vc.fillStyle = color;
    vc.fillRect(sx - (h / 2) * S, sy - (w / 2) * S, h * S, w * S);
  };
  // chasis
  rect(CAR.chasL / 2 - CAR.rearOverhang, 0, CAR.chasL, CAR.chasW, "rgba(90,100,125,0.85)");
  // ruedas
  for (const [wx, wy] of [[0, CAR.track/2], [0, -CAR.track/2], [CAR.wheelbase, CAR.track/2], [CAR.wheelbase, -CAR.track/2]])
    rect(wx, wy, CAR.wheelR * 2, CAR.wheelW, "#0c0f16");
  // LIDAR
  const [lx, ly] = carToScreen(CAR.laser.x, 0);
  vc.fillStyle = "#e05c5c"; vc.beginPath(); vc.arc(lx, ly, Math.max(0.035 * S, 3), 0, 2 * Math.PI); vc.fill();
  // ultrasonidos
  vc.fillStyle = "#38c8ff";
  for (const u of CAR.us) { const [ux, uy] = carToScreen(u.x, u.y); vc.beginPath(); vc.arc(ux, uy, Math.max(0.008 * S, 2.5), 0, 2 * Math.PI); vc.fill(); }
  // morro: flecha de sentido
  const [ax, ay] = carToScreen(CAR.chasL - CAR.rearOverhang + 0.03, 0);
  vc.fillStyle = "#8a93a6"; vc.beginPath();
  vc.moveTo(ax, ay); vc.lineTo(ax - 6, ay + 10); vc.lineTo(ax + 6, ay + 10); vc.closePath(); vc.fill();
}

/* ── sparklines IMU ── */
function drawSpark(canvas, buf, range) {
  const c = canvas.getContext("2d"), W = canvas.width, H = canvas.height;
  c.clearRect(0, 0, W, H);
  c.strokeStyle = "#1c2333"; c.beginPath(); c.moveTo(0, H / 2); c.lineTo(W, H / 2); c.stroke();
  const colors = ["#e05c5c", "#3fb96b", "#5aa2ff"];
  for (let k = 0; k < 3; k++) {
    c.strokeStyle = colors[k]; c.beginPath();
    buf.forEach((v, i) => {
      const x = (i / 149) * W, y = H / 2 - (v[k] / range) * (H / 2);
      i ? c.lineTo(x, y) : c.moveTo(x, y);
    });
    c.stroke();
  }
}

/* ── refresco de la UI ── */
function fresh(topic, maxMs) {
  const t = state.last[topic];
  return !t ? "red" : (Date.now() - t < maxMs ? "green" : "amber");
}
const fmt = (v, dec = 1) => (v === undefined || v === null) ? "—" : (+v).toFixed(dec);

function tick() {
  drawView();
  if (state.acc.length) {
    drawSpark($("#accSpark"), state.acc, 15);
    drawSpark($("#gyroSpark"), state.gyro, 5);
    const a = state.imu.linear_acceleration, g = state.imu.angular_velocity;
    $("#accVals").textContent = `${fmt(a.x)} ${fmt(a.y)} ${fmt(a.z)}`;
    $("#gyroVals").textContent = `${fmt(g.x,2)} ${fmt(g.y,2)} ${fmt(g.z,2)}`;
  }
  if (state.us) {
    $("#usL").textContent = fmt(state.us.left_distance, 0) + " cm";
    $("#usC").textContent = fmt(state.us.center_distance, 0) + " cm";
    $("#usR").textContent = fmt(state.us.right_distance, 0) + " cm";
    $("#usStop").classList.toggle("hidden", !state.us.emergency_stop);
  }
  if (state.energy) {
    $("#v1").textContent = fmt(state.energy.voltage_battery_1, 2) + " V";
    $("#v2").textContent = fmt(state.energy.voltage_battery_2, 2) + " V";
    $("#v3").textContent = fmt(state.energy.voltage_battery_3, 2) + " V";
    $("#cur").textContent = fmt(state.energy.current, 2) + " A";
  }
  $("#imuDot").className = "dot " + fresh("/imu", 1500);
  $("#usDot").className = "dot " + fresh("/ultrasound_data", 1500);
  $("#energyDot").className = "dot " + fresh("/energy", 3000);
  const list = $("#topicList"); list.innerHTML = "";
  for (const t of TOPICS) {
    const li = document.createElement("li");
    const age = state.last[t.name] ? ((Date.now() - state.last[t.name]) / 1000).toFixed(1) + " s" : "sin datos";
    li.innerHTML = `<code>${t.name}</code><span><span class="dot ${fresh(t.name, 3000)}"></span> ${age}</span>`;
    list.appendChild(li);
  }
  requestAnimationFrame(tick);
}

/* ── zoom ── */
document.querySelectorAll(".zoom button").forEach(b => b.onclick = () => {
  document.querySelectorAll(".zoom button").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  state.radius = parseFloat(b.dataset.r);
});

connect();
requestAnimationFrame(tick);
