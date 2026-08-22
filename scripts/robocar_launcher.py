#!/usr/bin/env python3
# robocar_launcher: servidor SIEMPRE-ACTIVO. Sirve el panel web (:8080) Y permite ARRANCAR/PARAR
# entornos desde la web sin SSH. Sobrevive a los cambios de stack (no lo mata stopall). Arranca al
# boot por cron:  @reboot bash -lc 'python3 ~/robocar/scripts/robocar_launcher.py >/tmp/launcher.log 2>&1'
#
#   GET /               -> panel estatico (index.html, etc.)
#   GET /api/start?env=banco|slam  -> stopall + bringup correspondiente
#   GET /api/stop       -> stopall
#   GET /api/status     -> {launching: env|stop|null}
import os, json, threading, time, subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

STATIC = os.path.expanduser('~/robocar/tools/car-panel/static')
SCRIPTS = os.path.expanduser('~/robocar/scripts')
ENVS = {'banco': 'bringupNAV2.sh', 'slam': 'bringupSLAM.sh', 'navreal': 'bringupNAVREAL.sh'}
state = {'launching': None}


def _san(x):
    return ''.join(c for c in (x or '') if c.isalnum() or c in '_-')


def _spawn(cmd, log):
    subprocess.Popen(['bash', '-lc', cmd], stdout=open(log, 'wb'),   # 'wb': log limpio por arranque
                     stderr=subprocess.STDOUT, start_new_session=True)


def _progress(env):
    """Lee el log del bringup activo y saca los pasos ('-> nodo') y si ha terminado."""
    steps, done, tail = [], False, ''
    try:
        txt = open('/tmp/launcher_%s.log' % env, encoding='utf-8', errors='replace').read()
        lines = txt.splitlines()
        for l in lines:
            s = l.strip()
            if s.startswith('-> '):
                steps.append(s[3:].strip())
        low = txt.lower()
        done = ('listo' in low) or ('lista' in low) or ('estado lifecycle' in low)
        tail = lines[-1].strip() if lines else ''
    except Exception:
        pass
    return {'steps': steps, 'count': len(steps), 'last': steps[-1] if steps else '',
            'done': done, 'tail': tail}


def start_env(env, arg=''):
    state['launching'] = env
    cmd = 'bash %s/stopall.sh; bash %s/%s' % (SCRIPTS, SCRIPTS, ENVS[env])
    if arg:
        cmd += ' ' + arg
    _spawn(cmd, '/tmp/launcher_%s.log' % env)
    threading.Thread(target=lambda: (time.sleep(40), state.update(launching=None)), daemon=True).start()


def stop_all():
    state['launching'] = 'stop'
    _spawn('bash %s/stopall.sh' % SCRIPTS, '/tmp/launcher_stop.log')
    threading.Thread(target=lambda: (time.sleep(4), state.update(launching=None)), daemon=True).start()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=STATIC, **k)

    def _json(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == '/api/start':
            q = parse_qs(p.query)
            env = (q.get('env', ['']))[0]
            mapa = _san((q.get('map', ['']))[0])
            if env in ENVS:
                start_env(env, mapa if env == 'navreal' else '')
                self._json({'ok': True, 'env': env, 'msg': 'arrancando ' + env})
            else:
                self._json({'ok': False, 'msg': 'entorno desconocido'})
            return
        if p.path == '/api/progress':
            env = (parse_qs(p.query).get('env', ['']))[0]
            if env not in ENVS:
                env = state['launching'] if state['launching'] in ENVS else ''
            pr = _progress(env) if env else {'steps': [], 'count': 0, 'last': '', 'done': False, 'tail': ''}
            pr.update({'ok': True, 'env': env, 'launching': state['launching']})
            self._json(pr); return
        if p.path == '/api/stop':
            stop_all(); self._json({'ok': True, 'msg': 'parando todo'}); return
        if p.path == '/api/status':
            self._json({'ok': True, 'launching': state['launching']}); return
        return super().do_GET()

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    print('robocar_launcher en :8080 (sirve panel + /api/start,/stop,/status)')
    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
