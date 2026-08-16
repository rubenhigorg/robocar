# -*- coding: utf-8 -*-
import io

# ---------------------------------------------------------------------------
# Nodos: id -> dict(cx, cy, w, cls, label, sub=None, bold=False)
# cls: sensor | odom | slam | ctrl | obs | out
N = {
  # capa 0 - fuentes (sensores + joy)
  'rplidar':   dict(cx=92,  cy=48,  w=150, cls='sensor', label='rplidar_node'),
  'encoder':   dict(cx=92,  cy=116, w=150, cls='sensor', label='encoder_node'),
  'accel':     dict(cx=92,  cy=184, w=180, cls='sensor', label='accelerometer_node'),
  'distance':  dict(cx=92,  cy=252, w=150, cls='sensor', label='distance_node'),
  'energy':    dict(cx=92,  cy=320, w=150, cls='sensor', label='energy_node'),
  'joy':       dict(cx=92,  cy=470, w=150, cls='ctrl',   label='joy_node'),
  # capa 1 - adaptadores / odometria laser / teleop
  'rf2o':      dict(cx=330, cy=48,  w=190, cls='odom',   label='rf2o_laser_odometry'),
  'wtc':       dict(cx=330, cy=116, w=190, cls='odom',   label='wheel_twistcov_node'),
  'teleop':    dict(cx=330, cy=470, w=200, cls='ctrl',   label='teleop_twist_joy_node'),
  # capa 2 - fusion / control
  'ekf':       dict(cx=585, cy=170, w=168, cls='odom',   label='ekf_filter_node', sub='TF odom→base_link', bold=True),
  'carctl':    dict(cx=585, cy=470, w=176, cls='ctrl',   label='car_control_node'),
  # capa 3 - slam / actuacion
  'carto':     dict(cx=810, cy=70,  w=186, cls='slam',   label='cartographer_node', sub='TF map→odom'),
  'pca':       dict(cx=885, cy=470, w=170, cls='out',    label='PCA9685 (I2C)'),
  # capa 4 - salidas
  'grid':      dict(cx=1095,cy=70,  w=190, cls='slam',   label='occupancy_grid_node'),
  'bridge':    dict(cx=1095,cy=300, w=190, cls='obs',    label='rosbridge_websocket'),
}
H = 34
HB = 42  # alto nodo bold

# Aristas: (src, dst, topic, style)  style: pipe | tele | obs | off
E = [
  ('rplidar','rf2o','/scan','pipe'),
  ('rplidar','carto','/scan','pipe'),
  ('encoder','wtc','/wheel_speed','pipe'),
  ('wtc','ekf','/wheel_speed_cov','pipe'),
  ('accel','ekf','/imu','pipe'),
  ('rf2o','ekf','/odom_rf2o','off'),
  ('ekf','carto','/odometry/filtered','pipe'),
  ('carto','grid','/submap_list','pipe'),
  ('joy','teleop','/joy','tele'),
  ('joy','carctl','/joy','tele'),
  ('teleop','carctl','/cmd_vel','tele'),
  ('carctl','pca','servo + ESC','tele'),
  # tomas de telemetria hacia el puente web (obs)
  ('rplidar','bridge','/scan','obs'),
  ('accel','bridge','/imu','obs'),
  ('distance','bridge','/ultrasound_data','obs'),
  ('energy','bridge','/energy','obs'),
  ('ekf','bridge','/odometry/filtered','obs'),
  ('grid','bridge','/map','obs'),
]

def box(n):
    d = N[n]; h = HB if (d.get('bold') or d.get('sub')) else H
    return dict(x=d['cx']-d['w']/2, y=d['cy']-h/2, w=d['w'], h=h, cx=d['cx'], cy=d['cy'])

def anchors(a, b):
    """Devuelve (x1,y1,x2,y2,c1x,c1y,c2x,c2y) para la bezier."""
    if b['x'] - (a['x']+a['w']) > -20:            # destino a la derecha
        x1,y1 = a['x']+a['w'], a['cy']
        x2,y2 = b['x'], b['cy']
        dx = max((x2-x1)*0.45, 30)
        return x1,y1,x2,y2, x1+dx,y1, x2-dx,y2
    elif b['cy'] > a['cy']:                        # destino abajo
        x1,y1 = a['cx'], a['y']+a['h']
        x2,y2 = b['cx'], b['y']
        dy = max((y2-y1)*0.5, 24)
        return x1,y1,x2,y2, x1,y1+dy, x2,y2-dy
    else:                                          # destino arriba
        x1,y1 = a['cx'], a['y']
        x2,y2 = b['cx'], b['y']+b['h']
        dy = max((y1-y2)*0.5, 24)
        return x1,y1,x2,y2, x1,y1-dy, x2,y2+dy

def bez_point(p, t):
    x1,y1,x2,y2,c1x,c1y,c2x,c2y = p
    mt=1-t
    x = mt*mt*mt*x1 + 3*mt*mt*t*c1x + 3*mt*t*t*c2x + t*t*t*x2
    y = mt*mt*mt*y1 + 3*mt*mt*t*c1y + 3*mt*t*t*c2y + t*t*t*y2
    return x,y

pipe_topics = set(t for _,_,t,st in E if st != 'obs')
edges_svg=[]; labels_svg=[]
for src,dst,topic,style in E:
    a,b = box(src), box(dst)
    p = anchors(a,b)
    x1,y1,x2,y2,c1x,c1y,c2x,c2y = p
    d = "M%.1f,%.1f C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (x1,y1,c1x,c1y,c2x,c2y,x2,y2)
    cls = {'pipe':'e-pipe','tele':'e-tele','obs':'e-obs','off':'e-off'}[style]
    mk  = 'arrO' if style=='obs' else 'arr'
    edges_svg.append('<path class="%s" d="%s" marker-end="url(#%s)"/>' % (cls,d,mk))
    # las tomas de telemetria solo se etiquetan si su topic no aparece ya en el flujo
    if style=='obs' and topic in pipe_topics:
        continue
    t = 0.30 if style=='obs' else 0.5
    lx,ly = bez_point(p,t)
    extra = '' if style!='off' else ' (desactivado)'
    lcls = 'lb-obs' if style=='obs' else ('lb-off' if style=='off' else 'lb')
    tw = (len(topic)+len(extra))*6.0 + 8
    labels_svg.append(
      '<g class="%s"><rect x="%.1f" y="%.1f" width="%.1f" height="15" rx="3"/>'
      '<text x="%.1f" y="%.1f">%s%s</text></g>'
      % (lcls, lx-tw/2, ly-7.5, tw, lx, ly+3.5, topic, extra))

nodes_svg=[]
for n,d in N.items():
    b = box(n); h = b['h']
    sub = d.get('sub')
    extra = ' n-bold' if d.get('bold') else ''
    nodes_svg.append('<g class="nd n-%s%s">' % (d['cls'], extra))
    nodes_svg.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="7"/>' % (b['x'],b['y'],b['w'],h))
    ty = b['cy']+4 if not sub else b['cy']-2
    nodes_svg.append('<text class="nt" x="%.1f" y="%.1f">%s</text>' % (b['cx'],ty,d['label']))
    if sub:
        nodes_svg.append('<text class="ns" x="%.1f" y="%.1f">%s</text>' % (b['cx'],b['cy']+12,sub))
    nodes_svg.append('</g>')

svg = []
svg.append('<div class="graph"><svg viewBox="0 0 1210 540" role="img" aria-label="Grafo de nodos y topics ROS2" xmlns="http://www.w3.org/2000/svg">')
svg.append('''<defs>
  <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
  <marker id="arrO" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mkO"/></marker>
</defs>''')
svg.append('<g class="edges">' + ''.join(edges_svg) + '</g>')
svg.append('<g class="elabels">' + ''.join(labels_svg) + '</g>')
svg.append('<g class="nodes">' + ''.join(nodes_svg) + '</g>')
svg.append('</svg></div>')
SVG = '\n'.join(svg)

# CSS del grafo (usa las variables :root ya definidas en la pagina)
CSS = '''
  /* --- grafo de nodos (SVG) --- */
  .graph{overflow-x:auto;margin:1rem 0 .4rem;padding:.4rem .2rem;-webkit-overflow-scrolling:touch}
  .graph svg{min-width:900px;width:100%;height:auto;font-family:var(--mono)}
  .graph .nd rect{fill:var(--surface);stroke:var(--line-2);stroke-width:1.4px;filter:drop-shadow(0 1px 1px rgba(0,0,0,.05))}
  .graph .n-sensor rect{fill:var(--sensor-bg);stroke:var(--sensor)}
  .graph .n-odom rect{fill:var(--odom-bg);stroke:var(--odom)}
  .graph .n-slam rect{fill:var(--slam-bg);stroke:var(--slam)}
  .graph .n-ctrl rect{fill:var(--ctrl-bg);stroke:var(--ctrl)}
  .graph .n-obs rect{fill:var(--obs-bg);stroke:var(--obs)}
  .graph .n-out rect{fill:var(--raise);stroke:var(--muted);stroke-dasharray:4 3}
  .graph .n-bold rect{stroke-width:2.6px}
  .graph .nt{text-anchor:middle;font-size:12px;font-weight:600;fill:var(--ink)}
  .graph .ns{text-anchor:middle;font-size:9.5px;fill:var(--muted);font-family:var(--sans)}
  .graph .edges path{fill:none}
  .graph .e-pipe{stroke:var(--odom);stroke-width:2px;opacity:.85}
  .graph .e-tele{stroke:var(--ctrl);stroke-width:2px;opacity:.85}
  .graph .e-obs{stroke:var(--faint);stroke-width:1.1px;stroke-dasharray:4 3;opacity:.5}
  .graph .e-off{stroke:var(--odom);stroke-width:1.6px;stroke-dasharray:2 3;opacity:.55}
  .graph .mk{fill:var(--odom)}
  .graph .mkO{fill:var(--faint)}
  .graph .lb text,.graph .lb-obs text,.graph .lb-off text{text-anchor:middle;font-size:10px}
  .graph .lb rect,.graph .lb-obs rect,.graph .lb-off rect{fill:var(--surface);opacity:.92}
  .graph .lb text{fill:var(--muted)}
  .graph .lb-obs text{fill:var(--faint);font-size:9px}
  .graph .lb-obs rect{opacity:.8}
  .graph .lb-off text{fill:var(--odom);opacity:.8}
  .graph .glegend{display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;font-size:.78rem;color:var(--muted);margin:.1rem 0 .3rem;font-family:var(--mono)}
  .graph .glegend b{color:var(--ink);font-weight:600}
'''

SECTION = '''  <h2>Diagrama del grafo: nodos y topics</h2>
  <div class="col"><p>Cada caja es un nodo (color = categor&iacute;a); cada flecha es un topic en sentido <b>publica&nbsp;&rarr;&nbsp;consume</b>. Las l&iacute;neas continuas azules/naranjas son el flujo principal (odometr&iacute;a y control); las <span style="color:var(--faint)">punteadas grises</span> son las tomas de telemetr&iacute;a que consume el puente web.</p></div>
''' + SVG + '''
  <div class="graph"><div class="glegend">
    <span><b style="color:var(--odom)">&mdash;</b> flujo odometr&iacute;a/SLAM</span>
    <span><b style="color:var(--ctrl)">&mdash;</b> teleop/control</span>
    <span><b style="color:var(--faint)">&middot;&middot;&middot;</b> telemetr&iacute;a &rarr; web</span>
    <span><b style="color:var(--odom)">&middot;&middot;</b> /odom_rf2o (fusi&oacute;n desactivada)</span>
  </div></div>

'''

p = "/home/lab/robocar/docs/tfm/nodos-ros2.html"
s = io.open(p, encoding="utf-8").read()

anchor_css = "  hr{border:0;border-top:1px solid var(--line);margin:2.2rem 0}\n"
assert anchor_css in s, "ancla CSS no encontrada"
s = s.replace(anchor_css, anchor_css + CSS, 1)

anchor_sec = '  <h2><span class="tag t-sensor">Sensores</span> Drivers de hardware'
assert anchor_sec in s, "ancla seccion no encontrada"
s = s.replace(anchor_sec, SECTION + anchor_sec, 1)

io.open(p,"w",encoding="utf-8").write(s)
io.open("/tmp/graph_preview.svg","w",encoding="utf-8").write(SVG)
print("nodos-ros2.html: diagrama SVG del grafo insertado (%d aristas, %d nodos)" % (len(E), len(N)))
