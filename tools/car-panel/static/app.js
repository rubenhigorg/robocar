/* Panel del Robocar — cliente rosbridge en vanilla JS, sin dependencias.
   Habla el protocolo JSON de rosbridge directamente por WebSocket. */

/* ── geometría real del coche (espejo del URDF, en metros) ── */
const CAR = {
  wheelbase: 0.175, track: 0.14, wheelR: 0.0325, wheelW: 0.026,
  chasL: 0.35, chasW: 0.175, rearOverhang: 0.085,
  laser: { x: 0.07, yaw: Math.PI },  // el 0º del C1 mira hacia atrás (montaje actual)
  // izq, centro, der — los laterales miran hacia afuera (~25º, TODO confirmar)
  us: [ { x: 0.24, y: 0.0525, yaw: 0.436 }, { x: 0.25, y: 0, yaw: 0 }, { x: 0.24, y: -0.0525, yaw: -0.436 } ],
};

const TOPICS = [
  { name: "/imu",             type: "sensor_msgs/msg/Imu",     throttle: 100 },
  { name: "/ultrasound_data", type: "messages_pkg/msg/Distance", throttle: 200 },
  { name: "/energy",          type: "messages_pkg/msg/Energy", throttle: 1000 },
  { name: "/scan",            type: "sensor_msgs/msg/LaserScan", throttle: 200 },
  { name: "/wheel_speed",     type: "geometry_msgs/msg/TwistStamped", throttle: 200 },
  { name: "/odometry/filtered", type: "nav_msgs/msg/Odometry", throttle: 150 },
];

const $ = s => document.querySelector(s);
const state = {
  imu: null, us: null, energy: null, scan: null, wheel: null, odom: null,
  last: {},              // topic -> timestamp ms
  acc: [], gyro: [], speed: [],  // buffers sparkline
  trail: [],             // trayectoria de la odometría EKF (frame odom)
  radius: 1.5,           // metros visibles desde el centro
};

const yawOf = q => Math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));

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
    else if (m.topic === "/wheel_speed") {
      state.wheel = m.msg;
      if (!state.odom) {           // sin EKF, la gráfica usa el encoder crudo
        state.speed.push([m.msg.twist.linear.x]);
        if (state.speed.length > 150) state.speed.shift();
      }
    }
    else if (m.topic === "/odometry/filtered") {
      state.odom = m.msg;
      state.speed.push([m.msg.twist.twist.linear.x]);   // gráfica: velocidad fusionada
      if (state.speed.length > 150) state.speed.shift();
      const p = m.msg.pose.pose.position;
      const last = state.trail[state.trail.length - 1];
      if (!last || Math.hypot(p.x - last[0], p.y - last[1]) > 0.01) {
        state.trail.push([p.x, p.y]);
        if (state.trail.length > 800) state.trail.shift();
      }
    }
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

  // estela de la trayectoria (odometría EKF, transformada al frame del coche)
  if (state.odom && state.trail.length > 1) {
    const pp = state.odom.pose.pose;
    const cx0 = pp.position.x, cy0 = pp.position.y, th = yawOf(pp.orientation);
    const cos = Math.cos(th), sin = Math.sin(th);
    const n = state.trail.length;
    vc.lineWidth = 2; vc.lineCap = "round";
    for (let i = 1; i < n; i++) {
      const a = state.trail[i - 1], b = state.trail[i];
      const ax = cos * (a[0] - cx0) + sin * (a[1] - cy0), ay = -sin * (a[0] - cx0) + cos * (a[1] - cy0);
      const bx = cos * (b[0] - cx0) + sin * (b[1] - cy0), by = -sin * (b[0] - cx0) + cos * (b[1] - cy0);
      const [x1, y1] = carToScreen(ax, ay), [x2, y2] = carToScreen(bx, by);
      vc.strokeStyle = `rgba(120,220,160,${(0.15 + 0.75 * i / n).toFixed(2)})`;
      vc.beginPath(); vc.moveTo(x1, y1); vc.lineTo(x2, y2); vc.stroke();
    }
    vc.lineWidth = 1;
  }

  // puntos LIDAR
  if (state.scan) {
    const sc = state.scan;
    vc.fillStyle = "#ff5252";
    for (let i = 0; i < sc.ranges.length; i++) {
      const r = sc.ranges[i];
      if (!isFinite(r) || r < sc.range_min || r > sc.range_max) continue;
      const a = sc.angle_min + i * sc.angle_increment + CAR.laser.yaw;
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
      const [e1x, e1y] = carToScreen(o.x + dist * Math.cos(o.yaw + spread), o.y + dist * Math.sin(o.yaw + spread));
      const [e2x, e2y] = carToScreen(o.x + dist * Math.cos(o.yaw - spread), o.y + dist * Math.sin(o.yaw - spread));
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
  const nSeries = buf.length ? buf[0].length : 0;
  for (let k = 0; k < nSeries; k++) {
    c.strokeStyle = colors[k]; c.beginPath();
    buf.forEach((v, i) => {
      const x = (i / 149) * W, y = H / 2 - (v[k] / range) * (H / 2);
      i ? c.lineTo(x, y) : c.moveTo(x, y);
    });
    c.stroke();
  }
}

/* ── batería: % estimado desde la tensión del pack 3S (curva LiPo en reposo) ── */
const SOC_CURVE = [[10.5,0],[10.8,10],[11.1,20],[11.5,40],[11.8,60],[12.0,75],[12.3,90],[12.6,100]];
function socFromVoltage(v) {
  if (v <= SOC_CURVE[0][0]) return 0;
  if (v >= SOC_CURVE[SOC_CURVE.length-1][0]) return 100;
  for (let i = 1; i < SOC_CURVE.length; i++) {
    const [v0,p0] = SOC_CURVE[i-1], [v1,p1] = SOC_CURVE[i];
    if (v <= v1) return Math.round(p0 + (p1-p0) * (v-v0) / (v1-v0));
  }
  return 100;
}
function updateBattery() {
  const el = $("#batt");
  if (!state.energy || fresh("/energy", 5000) !== "green") {
    el.className = "batt unknown"; $("#battPct").textContent = "—";
    $("#battFill").setAttribute("width", 0); return;
  }
  const v = state.energy.voltage_battery_1;
  const pct = socFromVoltage(v);
  $("#battFill").setAttribute("width", (22 * pct / 100).toFixed(1));
  $("#battPct").textContent = pct + "%";
  el.className = "batt " + (pct > 50 ? "ok" : pct > 20 ? "warn" : "bad");
  el.title = `batería del coche: ${v.toFixed(2)} V (pack 3S)`;
}

/* ── refresco de la UI ── */
function fresh(topic, maxMs) {
  const t = state.last[topic];
  return !t ? "red" : (Date.now() - t < maxMs ? "green" : "amber");
}
const fmt = (v, dec = 1) => (v === undefined || v === null) ? "—" : (+v).toFixed(dec);

function tick() {
  drawView();
  drawOdomWorld();
  if (state.acc.length) {
    drawSpark($("#accSpark"), state.acc, 15);
    drawSpark($("#gyroSpark"), state.gyro, 5);
    const a = state.imu.linear_acceleration, g = state.imu.angular_velocity;
    $("#accVals").textContent = `${fmt(a.x)} ${fmt(a.y)} ${fmt(a.z)}`;
    $("#gyroVals").textContent = `${fmt(g.x,2)} ${fmt(g.y,2)} ${fmt(g.z,2)}`;
  }
  if (state.us) {
    const usTxt = v => (v == null) ? "—" : (v < 0 ? "✕ sin señal" : fmt(v, 0) + " cm");
    $("#usL").textContent = usTxt(state.us.left_distance);
    $("#usC").textContent = usTxt(state.us.center_distance);
    $("#usR").textContent = usTxt(state.us.right_distance);
    $("#usStop").classList.toggle("hidden", !state.us.emergency_stop);
  }
  if (state.energy) {
    $("#v1").textContent = fmt(state.energy.voltage_battery_1, 2) + " V";
    $("#v2").textContent = fmt(state.energy.voltage_battery_2, 2) + " V";
    $("#v3").textContent = fmt(state.energy.voltage_battery_3, 2) + " V";
    $("#cur").textContent = fmt(state.energy.current, 2) + " A";
  }
  if (state.odom) {
    const v = state.odom.twist.twist.linear.x;
    $("#speedVal").textContent = fmt(v, 2);
    $("#speedKmh").textContent = fmt(v * 3.6, 1) + " km/h";
    const pp = state.odom.pose.pose;
    $("#odomPose").textContent =
      `x ${fmt(pp.position.x, 2)} m · y ${fmt(pp.position.y, 2)} m · θ ${fmt(yawOf(pp.orientation) * 180 / Math.PI, 0)}°`;
    if (state.wheel) $("#speedRaw").textContent = `encoder crudo: ${fmt(state.wheel.twist.linear.x, 2)} m/s`;
    drawSpark($("#speedSpark"), state.speed, 1.0);
  } else if (state.wheel) {
    const v = state.wheel.twist.linear.x;
    $("#speedVal").textContent = fmt(v, 2);
    $("#speedKmh").textContent = fmt(v * 3.6, 1) + " km/h";
    $("#odomPose").textContent = "(EKF sin datos — mostrando encoder crudo)";
    drawSpark($("#speedSpark"), state.speed, 1.0);
  }
  $("#speedDot").className = "dot " + (state.odom ? fresh("/odometry/filtered", 1500) : fresh("/wheel_speed", 2000));
  updateBattery();
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


/* -- vista de odometria en el frame odom (mundo fijo, el coche se mueve) -- */
function niceStep(v) {
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  const f = v / p;
  return (f < 1.5 ? 1 : f < 3.5 ? 2 : f < 7.5 ? 5 : 10) * p;
}

function drawOdomWorld() {
  const cv = document.getElementById("odomWorld");
  if (!cv) return;
  const g = cv.getContext("2d"), W = cv.width, H = cv.height;
  g.clearRect(0, 0, W, H);

  if (state.odom) {
    const p = state.odom.pose.pose;
    $("#odomBig").textContent =
      `x ${fmt(p.position.x, 2)} · y ${fmt(p.position.y, 2)} m · θ ${fmt(yawOf(p.orientation) * 180 / Math.PI, 0)}°`;
    $("#odomDot").className = "dot " + fresh("/odometry/filtered", 1500);
  } else {
    $("#odomBig").textContent = "sin datos EKF";
  }

  const pts = state.trail.slice();
  pts.push([0, 0]);
  if (state.odom) { const p = state.odom.pose.pose.position; pts.push([p.x, p.y]); }
  let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
  for (const q of pts) { if (q[0] < minx) minx = q[0]; if (q[0] > maxx) maxx = q[0]; if (q[1] < miny) miny = q[1]; if (q[1] > maxy) maxy = q[1]; }
  const cx = (minx + maxx) / 2, cy = (miny + maxy) / 2;
  const span = Math.max(maxx - minx, maxy - miny, 0.5) * 1.3;
  const S = Math.min(W, H) / span;
  const toS = (x, y) => [W / 2 - (y - cy) * S, H / 2 - (x - cx) * S];

  const step = niceStep(span / 4);
  g.strokeStyle = "#1c2333"; g.fillStyle = "#4a5578"; g.font = "10px system-ui"; g.lineWidth = 1;
  for (let gx = Math.ceil((cx - span / 2) / step) * step; gx <= cx + span / 2 + 1e-6; gx += step) {
    const sy = toS(gx, cy)[1];
    g.beginPath(); g.moveTo(0, sy); g.lineTo(W, sy); g.stroke();
    g.fillText(gx.toFixed(1), 2, sy - 2);
  }
  for (let gy = Math.ceil((cy - span / 2) / step) * step; gy <= cy + span / 2 + 1e-6; gy += step) {
    const sx = toS(cx, gy)[0];
    g.beginPath(); g.moveTo(sx, 0); g.lineTo(sx, H); g.stroke();
  }

  const o = toS(0, 0);
  g.fillStyle = "#5b6b8c"; g.beginPath(); g.arc(o[0], o[1], 3, 0, 6.283); g.fill();
  g.fillText("origen", o[0] + 5, o[1] + 12);

  if (state.trail.length > 1) {
    g.strokeStyle = "#78dca0"; g.lineWidth = 2; g.lineJoin = "round"; g.beginPath();
    for (let i = 0; i < state.trail.length; i++) {
      const s = toS(state.trail[i][0], state.trail[i][1]);
      i ? g.lineTo(s[0], s[1]) : g.moveTo(s[0], s[1]);
    }
    g.stroke(); g.lineWidth = 1;
  }

  if (state.odom) {
    const p = state.odom.pose.pose, th = yawOf(p.orientation);
    const hx = Math.cos(th), hy = Math.sin(th), lx = -hy, ly = hx;
    const L = 0.11, Wd = 0.06, x = p.position.x, y = p.position.y;
    const tip = toS(x + hx * L, y + hy * L);
    const bl = toS(x - hx * L * 0.5 + lx * Wd, y - hy * L * 0.5 + ly * Wd);
    const br = toS(x - hx * L * 0.5 - lx * Wd, y - hy * L * 0.5 - ly * Wd);
    g.fillStyle = "#8affce";
    g.beginPath(); g.moveTo(tip[0], tip[1]); g.lineTo(bl[0], bl[1]); g.lineTo(br[0], br[1]); g.closePath(); g.fill();
  }
}
