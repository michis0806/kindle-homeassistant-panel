#!/usr/bin/env python3
"""Kindle controls and optional incremental live view. Credentials stay here."""
import copy
from decimal import Decimal, InvalidOperation
import ui
import ha_dashboard
import hashlib
import hmac
import html
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError

DOMAINS = {'light', 'switch', 'input_boolean', 'scene', 'sensor', 'binary_sensor', 'climate', 'weather'}
COOKIE = 'kindle_panel_device'

def esc(value):
    return html.escape(str(value), quote=True)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def valid_entity(value):
    return bool(re.fullmatch(r'[a-z_]+\.[a-z0-9_]+', value)) and value.split('.')[0] in DOMAINS

class App:
    def __init__(self, directory, api=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory / 'panel.json'
        self.lock = threading.RLock()
        self.live_lock = threading.Lock()
        self.live_cache = None
        self.panel_lock = threading.RLock()
        self.panel_cache = None
        self.panel_caches = {}
        self.unit_cache = None
        self.state_cache = None
        self.dashboard_source = None
        self.dashboard_stop = threading.Event()
        self.api_override = api
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {
            'admin_csrf': secrets.token_hex(24), 'entities': [], 'devices': {}}
        options = self.directory / 'options.json'
        self.refresh = max(10, min(300, int(json.loads(options.read_text()).get('refresh_seconds', 30)))) if options.exists() else 30
        self.save()

    def save(self):
        with self.lock:
            temporary = self.path.with_suffix('.tmp')
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as stream:
                json.dump(self.data, stream)
            os.replace(temporary, self.path)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.data)

    def start_dashboard_source(self):
        self.dashboard_source=ha_dashboard.Source()
        bootstrap_needed=True
        def refresh():
            nonlocal bootstrap_needed
            raw=self.snapshot()
            paths={ha_dashboard.PATH}|{d.get('dashboard_path',ha_dashboard.PATH) for d in raw['devices'].values() if d['approved']}
            try:
                self.dashboard_source.refresh(raw,paths,bootstrap=bootstrap_needed)
                bootstrap_needed=False
                with self.dashboard_source.lock:self.dashboard_source.errors.pop('connection',None)
            except Exception as error:
                with self.dashboard_source.lock:
                    self.dashboard_source.errors['connection']=type(error).__name__
        refresh()
        def loop():
            while not self.dashboard_stop.wait(5):refresh()
        threading.Thread(target=loop,daemon=True).start()

    def access_config(self, token=None):
        base=self.snapshot()
        if self.dashboard_source is None or not base.get('dashboard_enabled',True):return base
        device=self.device(token or '') or {}
        path=device.get('dashboard_path',ha_dashboard.PATH)
        model=self.dashboard_source.model(path)
        base.update(entities=model['entities'],control_entities=model['control_entities'],dashboard_path=path,default_view=device.get('view_path'))
        return base

    def render_config(self, token=None, view_path=None):
        base=self.access_config(token)
        if self.dashboard_source is None or not base.get('dashboard_enabled',True):return base
        model=self.dashboard_source.model(base['dashboard_path'])
        return ha_dashboard.view_config(base,model,view_path or base.get('default_view'))

    def assign_dashboard(self,key,path,name,view_path=None):
        if self.dashboard_source is None:raise ValueError('Dashboard connection unavailable')
        available={d['url_path'] for d in self.dashboard_source.status()['dashboards']}
        if path not in available or len(name)>60:raise ValueError('Invalid dashboard assignment')
        self.dashboard_source.refresh(self.snapshot(),{path})
        model=self.dashboard_source.model(path)
        if view_path not in {v['path'] for v in model['views']}:view_path=None
        with self.lock:
            if key not in self.data['devices']:raise ValueError('Unknown device')
            self.data['devices'][key].update(dashboard_path=path,name=name.strip(),view_path=view_path)
            self.save()

    def bind_controller(self,token,controller):
        if not re.fullmatch(r'[a-f0-9]{32}',controller):raise ValueError('Invalid controller ID')
        with self.lock:
            device=self.data['devices'].get(digest(token))
            if not device or not device['approved']:raise PermissionError()
            if device.get('controller_id') and device['controller_id']!=controller:raise PermissionError()
            device['controller_id']=controller
            self.save()
        return self.device(token)

    def api(self, path, payload=None):
        if self.api_override:
            return self.api_override(path, payload)
        token = os.environ.get('SUPERVISOR_TOKEN', '')
        if not token:
            raise RuntimeError('Core API unavailable')
        request = Request('http://supervisor/core/api/' + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        with urlopen(request, timeout=8) as response:
            return json.load(response)

    def states(self):
        return {item['entity_id']: item for item in self.api('states')}

    def live_snapshot(self, token=None):
        config = self.access_config(token)
        selected = [entity for entity in config['entities'] if entity.startswith('sensor.')]
        cache_key = (tuple(selected), json.dumps(config.get('labels', {}), sort_keys=True))
        with self.live_lock:
            now = time.monotonic()
            if self.live_cache and self.live_cache[0] == cache_key and now - self.live_cache[1] < 1.5:
                return self.live_cache[2]
            readings = []
            for entity in selected:
                item = self.api('states/' + entity)
                attrs = item.get('attributes', {})
                value = str(item.get('state', 'unavailable'))
                available = value not in {'unknown', 'unavailable'}
                readings.append({'entity': entity, 'label': ui.label(config, entity, item),
                    'value': ui.number(value) if available else ui.display_state('sensor', value, attrs),
                    'unit': str(attrs.get('unit_of_measurement', '')) if available else '',
                    'available': available})
            # ui helpers escape HTML; the JSON values are plain text for text nodes.
            for item in readings:
                item['value'] = html.unescape(item['value'])
            result = {'readings': readings, 'interval_ms': 2000}
            self.live_cache = (cache_key, time.monotonic(), result)
            return result

    def panel_snapshot(self, token=None, view_path=None):
        config = self.render_config(token,view_path)
        key = (tuple(config['entities']), json.dumps(config.get('labels', {}), sort_keys=True), config.get('dashboard_path'), config.get('dashboard_revision'),config.get('dashboard_view',{}).get('path',view_path))
        with self.panel_lock:
            now = time.monotonic()
            if self.panel_cache is None:self.panel_caches.clear()
            cached=self.panel_caches.get(key)
            if cached and now-cached[0]<1.5:return cached[1]
            if self.panel_cache is None:self.state_cache=None
            if not self.state_cache or now-self.state_cache[0]>=1.5:
                self.state_cache=(now,self.states())
            states={entity:copy.deepcopy(self.state_cache[1].get(entity,{'state':'unavailable','attributes':{}})) for entity in config['entities']}
            if any(entity.startswith('climate.') for entity in config['entities']):
                if not self.unit_cache or now - self.unit_cache[0] > 60:
                    self.unit_cache = (now, self.api('config').get('unit_system', {}).get('temperature', ''))
                for entity, item in states.items():
                    if entity.startswith('climate.'):
                        item.setdefault('attributes', {})['temperature_unit'] = self.unit_cache[1]
            result = ui.updates(config, states)
            if config.get('dashboard_revision'):result['revision']=config['dashboard_revision']
            self.panel_cache = (key, time.monotonic(), result)
            self.panel_caches[key]=(time.monotonic(),result)
            if len(self.panel_caches)>64:self.panel_caches.pop(next(iter(self.panel_caches)))
            return result

    def request_kiosk_exit(self, token, csrf, controller=None):
        device = self.device(token)
        if not device or not device['approved'] or not hmac.compare_digest(device['csrf'], csrf):
            raise PermissionError()
        with self.lock:
            expected=device.get('controller_id','')
            if (controller or '')!=expected:raise PermissionError()
            if expected:
                generations=self.data.setdefault('exit_generations',{})
                generations[expected]=int(generations.get(expected,0))+1
            else:
                self.data['exit_generation'] = int(self.data.get('exit_generation', 0)) + 1
            self.save()

    def device(self, token):
        with self.lock:
            item = self.data['devices'].get(digest(token))
            return copy.deepcopy(item) if item else None

    def register(self, ip):
        with self.lock:
            now = time.time()
            self.data['devices'] = {key: value for key, value in self.data['devices'].items()
                if value['approved'] or now - value['created'] < 3600}
            if len(self.data['devices']) >= 32:
                raise ValueError('Device limit')
            token = secrets.token_hex(32)
            used = {value['code'] for value in self.data['devices'].values()}
            code = str(secrets.randbelow(900000) + 100000)
            while code in used:
                code = str(secrets.randbelow(900000) + 100000)
            self.data['devices'][digest(token)] = {'code': code, 'ip': ip, 'approved': False,
                'created': now, 'csrf': secrets.token_hex(24)}
            self.save()
            return token, self.device(token)

    def set_entities(self, values, labels=None):
        available = self.states()
        selected = list(dict.fromkeys(value for value in values if value))
        if len(selected) > 8 or any(not valid_entity(value) or value not in available for value in selected):
            raise ValueError('Invalid entity selection')
        with self.lock:
            previous = self.data.get('labels', {}) if labels is None else labels
            if any(len(value) > 60 for value in previous.values()):
                raise ValueError('Label too long')
            self.data['entities'] = selected
            self.data['labels'] = {key: value.strip() for key, value in previous.items() if key in selected and value.strip()}
            self.save()

    def control(self, token, csrf, entity, action, value=''):
        device = self.device(token)
        if not device or not device['approved'] or not hmac.compare_digest(device['csrf'], csrf):
            raise PermissionError()
        config=self.access_config(token)
        if entity not in config['entities'] or ('control_entities' in config and entity not in config['control_entities']):
            raise ValueError('Entity is not selected')
        domain = entity.split('.')[0]
        item = self.states().get(entity)
        if item is None or item['state'] == 'unavailable' or (item['state'] == 'unknown' and domain != 'scene'):
            raise ValueError('Entity unavailable')
        payload = {'entity_id': entity}
        if domain == 'climate':
            attrs = item.get('attributes', {})
            features = int(attrs.get('supported_features', 0))
            if len(value) > 64:
                raise ValueError('Invalid value')
            if action == 'climate_temperature' and features & 1:
                try:
                    requested = Decimal(value.replace(',', '.'))
                    minimum = Decimal(str(attrs['min_temp']))
                    maximum = Decimal(str(attrs['max_temp']))
                    step = Decimal(str(attrs.get('target_temp_step', 0.5)))
                    if not all(v.is_finite() for v in (requested, minimum, maximum, step)) or step <= 0:
                        raise ValueError('Invalid temperature')
                    if requested < minimum or requested > maximum or (requested - minimum) % step != 0:
                        raise ValueError('Temperature outside supported range/step')
                except (InvalidOperation, KeyError, TypeError):
                    raise ValueError('Invalid temperature')
                service = 'set_temperature'
                payload['temperature'] = float(requested)
            elif action == 'climate_hvac' and value in attrs.get('hvac_modes', []):
                service = 'set_hvac_mode'
                payload['hvac_mode'] = value
            elif action == 'climate_fan' and features & 8 and value in attrs.get('fan_modes', []):
                service = 'set_fan_mode'
                payload['fan_mode'] = value
            else:
                raise ValueError('Climate action not supported')
        else:
            allowed = {'turn_on', 'turn_off'} if domain in {'light', 'switch', 'input_boolean'} else {'activate'} if domain == 'scene' else set()
            if action not in allowed:
                raise ValueError('Action not allowed')
            service = 'turn_on' if action == 'activate' else action
        self.api('services/' + domain + '/' + service, payload)
        with self.panel_lock:
            self.panel_cache = None

CSS = ui.CSS

def page(title, body, refresh=0, kindle=False):
    meta = '<meta http-equiv="refresh" content="%d">' % refresh if refresh else ''
    return ('<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">' + meta +
        '<title>' + esc(title) + '</title><style>' + CSS + '</style></head><body' + (' class="kindle"' if kindle else '') + '>' + body + '</body></html>')

class Handler(BaseHTTPRequestHandler):
    server_version = 'KindlePanel/0.5'
    def log_message(self, *args):
        pass

    @property
    def app(self):
        return self.server.app

    def admin(self):
        return (self.server.admin and self.client_address[0] == self.server.ingress_ip
            and bool(self.headers.get('X-Remote-User-Id')))

    def send(self, status, content, cookie=None, content_type='text/html; charset=utf-8'):
        data = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; frame-src 'self'; script-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'self'")
        if cookie:
            self.send_header('Set-Cookie', COOKIE + '=' + cookie + '; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000')
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location='./'):
        self.send_response(303)
        self.send_header('Location', location)
        self.send_header('Content-Length', '0')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def token(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get('Cookie', ''))
            token = jar[COOKIE].value if COOKIE in jar else ''
            return token if re.fullmatch(r'[0-9a-f]{64}', token) else ''
        except cookies.CookieError:
            return ''

    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if self.server.admin:
                if not self.admin() or path not in {'/admin/','/admin/preview'}:
                    return self.send(403, page('Kein Zugriff', '<h1>Kein Zugriff</h1>'))
                if path=='/admin/preview':return self.send(200,self.dashboard_preview())
                return self.send(200, self.admin_page())
            if path == '/kiosk-status':
                # Public read-only opaque counter, containing no device/entity data.
                # Mutating it requires the paired session and CSRF below.
                controller=parse_qs(urlsplit(self.path).query).get('controller',[''])[0]
                raw=self.app.snapshot()
                counter=raw.get('exit_generations',{}).get(controller,0) if controller else raw.get('exit_generation',0)
                return self.send(200,str(counter),content_type='text/plain; charset=utf-8')
            if path == '/health':
                self.app.api('')
                return self.send(200, page('OK', 'OK'))
            if path in {'/live', '/live.json', '/live.js', '/updates.json', '/panel.js'}:
                device = self.app.device(self.token())
                if not device or not device['approved']:
                    return self.send(403, json.dumps({'error': 'pairing_required'}), content_type='application/json')
                if path == '/updates.json':
                    try:
                        return self.send(200, json.dumps(self.app.panel_snapshot(self.token(),parse_qs(urlsplit(self.path).query).get('view',[None])[0])), content_type='application/json')
                    except Exception:
                        return self.send(503, json.dumps({'error':'upstream_unavailable'}), content_type='application/json')
                if path == '/panel.js':
                    return self.send(200, (Path(__file__).parent / 'panel.js').read_text(), content_type='application/javascript; charset=utf-8')
                if path == '/live.json':
                    try:
                        return self.send(200, json.dumps(self.app.live_snapshot(self.token())), content_type='application/json')
                    except Exception:
                        return self.send(503, json.dumps({'error': 'upstream_unavailable'}), content_type='application/json')
                if path == '/live.js':
                    return self.send(200, (Path(__file__).parent / 'live.js').read_text(), content_type='application/javascript; charset=utf-8')
                body = ('<div class="panel"><div class="climate-main"><a class="back" href="./">‹ Übersicht</a>'
                    '<div class="topline">Live-Test</div><h1>Temperatur &amp; Strom</h1>'
                    '<p id="live-status" role="status">Live-Verbindung wird gestartet …</p>'
                    '<div id="live-readings"></div><noscript><p>JavaScript ist deaktiviert.</p></noscript>'
                    '<p class="climate-foot">Die Werte werden alle zwei Sekunden abgefragt. '
                    'Nur geänderte Anzeigen werden aktualisiert; diese Seite lädt nicht automatisch neu.</p>'
                    '</div></div><script src="/live.js"></script>')
                return self.send(200, page('Live-Test', body, kindle=True))
            if path != '/':
                return self.send(404, page('Nicht gefunden', 'Nicht gefunden'))
            token = self.token()
            device = self.app.device(token)
            new_token = None
            if not device:
                new_token, device = self.app.register(self.client_address[0])
            if not device['approved']:
                body = '<h1>Kindle verbinden</h1><p>Öffne auf dem Computer in Home Assistant die App <b>Kindle Panel</b> und deren Weboberfläche. Gib dort diesen Kindle frei:</p><p class="code">' + esc(device['code']) + '</p><p>Diese Seite aktualisiert sich automatisch.</p>'
                return self.send(200, page('Kindle verbinden', body, 10), new_token)
            controller=parse_qs(urlsplit(self.path).query).get('controller',[''])[0]
            if controller:device=self.app.bind_controller(token,controller)
            climate_entity = parse_qs(urlsplit(self.path).query).get('klima', [''])[0]
            if climate_entity:
                if climate_entity not in self.app.access_config(token)['entities'] or not climate_entity.startswith('climate.'):
                    return self.send(404, page('Nicht ausgewählt', '<h1>Dieses Gerät ist nicht ausgewählt.</h1><a href="./">Zur Übersicht</a>'))
                item = self.app.states().get(climate_entity, {'state':'unavailable','attributes':{}})
                item = copy.deepcopy(item)
                item.setdefault('attributes', {})['temperature_unit'] = self.app.api('config').get('unit_system', {}).get('temperature', '')
                return self.send(200, page('Raumklima', ui.climate(self.app.render_config(token,parse_qs(urlsplit(self.path).query).get('view',[None])[0]), climate_entity, item, device), kindle=True))
            return self.send(200, self.dashboard(device))
        except Exception:
            device=self.app.device(self.token()) if not self.server.admin else None
            exit_button=ui.exit_form(device) if device and device['approved'] else ''
            self.send(503, page('Verbindung unterbrochen',exit_button+ '<h1>Home Assistant vorübergehend nicht erreichbar</h1><p><a href="./">Erneut versuchen</a></p>', 30))

    def do_POST(self):
        json_action = urlsplit(self.path).path == '/action.json' and not self.server.admin
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size <= 0 or size > 16384:
                raise ValueError()
            data = parse_qs(self.rfile.read(size).decode('utf-8'), keep_blank_values=True)
            field = lambda name: data.get(name, [''])[0]
            path = urlsplit(self.path).path
            if self.server.admin:
                if not self.admin() or not hmac.compare_digest(field('csrf'), self.app.snapshot()['admin_csrf']):
                    raise PermissionError()
                if path == '/admin/save':
                    self.app.set_entities([field('entity' + str(i)) for i in range(8)], {field('entity' + str(i)): field('label' + str(i)) for i in range(8) if field('entity' + str(i))})
                elif path == '/admin/assign':
                    self.app.assign_dashboard(field('device'),field('dashboard'),field('name'),field('view'))
                elif path in {'/admin/approve', '/admin/revoke'}:
                    key = field('device')
                    with self.app.lock:
                        if key not in self.app.data['devices']:
                            raise ValueError()
                        if path.endswith('/approve'):
                            self.app.data['devices'][key]['approved'] = True
                        else:
                            del self.app.data['devices'][key]
                        self.app.save()
                else:
                    raise ValueError()
            else:
                if path == '/kiosk-exit':
                    self.app.request_kiosk_exit(self.token(), field('csrf'), field('controller'))
                    return self.send(200, page('Kindle verlassen', '<h1>Kindle wird beendet …</h1><p>Die Kindle-Startseite sollte gleich erscheinen.</p><p><a href="./">Zur Übersicht</a></p>', kindle=True))
                if path not in {'/action', '/action.json'}:
                    raise PermissionError()
                self.app.control(self.token(), field('csrf'), field('entity'), field('action'), field('value'))
                if json_action:
                    return self.send(202, json.dumps({'accepted':True}), content_type='application/json')
                if field('entity').startswith('climate.'):
                    return self.redirect('./?klima=' + field('entity'))
                page_index = field('seite')
                if page_index.isdigit() and 0 <= int(page_index) < 8:
                    return self.redirect('./?seite=' + page_index)
            self.redirect()
        except PermissionError:
            if json_action: return self.send(403, json.dumps({'error':'not_authorized'}), content_type='application/json')
            self.send(403, page('Nicht freigegeben', '<h1>Aktion nicht freigegeben</h1><p><a href="./">Zurück</a></p>'))
        except ValueError:
            if json_action: return self.send(400, json.dumps({'error':'invalid_action'}), content_type='application/json')
            self.send(400, page('Aktion nicht möglich', '<h1>Aktion nicht möglich</h1><p>Bitte aktualisieren und erneut versuchen.</p><a href="./">Zurück</a>'))
        except Exception:
            if json_action: return self.send(503, json.dumps({'error':'upstream_unavailable'}), content_type='application/json')
            self.send(503, page('Verbindungsfehler', '<h1>Home Assistant antwortet nicht</h1><p>Bitte Zustand prüfen, bevor du die Aktion wiederholst.</p><a href="./">Aktualisieren</a>'))

    def dashboard(self, device):
        try:
            page_index = int(parse_qs(urlsplit(self.path).query).get('seite', ['0'])[0])
        except ValueError:
            page_index = 0
        config = self.app.render_config(self.token(),parse_qs(urlsplit(self.path).query).get('view',[None])[0])
        states = self.app.states()
        if any(entity.startswith('climate.') for entity in config['entities']):
            unit = self.app.api('config').get('unit_system', {}).get('temperature', '')
            for entity in config['entities']:
                if entity.startswith('climate.') and entity in states:
                    states[entity].setdefault('attributes', {})['temperature_unit'] = unit
        body = ui.dashboard(config, states, device, page_index, self.app.refresh)
        return page('Zuhause', body, kindle=True)

    def dashboard_preview(self):
        query=parse_qs(urlsplit(self.path).query)
        raw=self.app.snapshot();key=query.get('device',[''])[0]
        device=raw['devices'].get(key,{})
        path=device.get('dashboard_path',ha_dashboard.PATH)
        if self.app.dashboard_source:
            self.app.dashboard_source.refresh(raw,{path})
            model=self.app.dashboard_source.model(path)
            config=ha_dashboard.view_config(raw,model,query.get('view',[None])[0])
        else:config=raw
        states=self.app.states()
        unit=self.app.api('config').get('unit_system',{}).get('temperature','')
        for entity,item in states.items():
            if entity.startswith('climate.'):item.setdefault('attributes',{})['temperature_unit']=unit
        try:index=int(query.get('seite',['0'])[0])
        except ValueError:index=0
        body=ui.dashboard(config,states,{'csrf':'preview-only'},index,self.app.refresh)
        body=re.sub(r'<script\b[^>]*>.*?</script>','',body,flags=re.S)
        body=body.replace('Live-Verbindung wird gestartet …','Vorschau')
        body=re.sub(r'<form\b[^>]*>','<div>',body)
        body=body.replace('</form>','</div>')
        # No forms and no scripts: preview buttons cannot send commands.
        if key:
            body=re.sub(r'href="\?([^"]*)"',lambda m:'href="?device='+esc(key)+'&amp;'+m.group(1)+'"',body)
        return page('Kindle-Vorschau',body,kindle=True)

    def admin_page(self):
        config=self.app.snapshot()
        csrf='<input type="hidden" name="csrf" value="'+esc(config['admin_csrf'])+'">'
        source=self.app.dashboard_source
        status=source.status() if source else {'dashboards':[],'errors':{},'warnings':{}}
        body='<h1>Kindle Panel</h1><p>Gestalte das Layout direkt in Home Assistant. Hier ordnest du jedem Kindle sein Dashboard zu und prüfst die Kindle-Vorschau.</p>'
        if source:
            body+='<p><a href="/'+ha_dashboard.PATH+'" target="_top">Kindle-Dashboard in Home Assistant öffnen</a></p>'
            for path,error in status['errors'].items():body+='<p class="notice">Dashboard '+esc(path)+': '+esc(error)+'</p>'
        if not config['devices']:
            body+='<p>Öffne die Kindle-Adresse auf dem Gerät. Hier erscheint danach sein Freigabecode.</p>'
        body+='<h2>Kindles und Dashboards</h2>'
        for key,device in config['devices'].items():
            name=device.get('name') or 'Kindle '+device['code']
            body+='<section style="border:1px solid #aaa;padding:16px;margin:12px 0"><h3>'+esc(name)+'</h3><p>Code '+esc(device['code'])+' · '+esc(device['ip'])+(' · Freigegeben' if device['approved'] else ' · Wartet auf Freigabe')+'</p>'
            if device['approved'] and source:
                body+='<form method="post" action="assign">'+csrf+'<input type="hidden" name="device" value="'+esc(key)+'"><label>Gerätename <input name="name" maxlength="60" value="'+esc(device.get('name',''))+'" placeholder="Zum Beispiel Büro"></label><label>Dashboard <select name="dashboard">'
                selected=device.get('dashboard_path',ha_dashboard.PATH)
                for dashboard in status['dashboards']:
                    path=dashboard['url_path'];body+='<option value="'+esc(path)+'"'+(' selected' if path==selected else '')+'>'+esc(dashboard.get('title',path))+'</option>'
                body+='</select></label><label>Startansicht <select name="view"><option value="">Erste Ansicht</option>'
                try:views=source.model(selected)['views']
                except RuntimeError:views=[]
                for view in views:body+='<option value="'+esc(view['path'])+'"'+(' selected' if view['path']==device.get('view_path') else '')+'>'+esc(view['title'])+'</option>'
                body+='</select></label><button>Zuordnung speichern</button></form>'
                if not device.get('controller_id'):body+='<p class="muted">Bisheriger Starter ohne Gerätekennung. Für zusätzliche Kindles den neuen Installer verwenden.</p>'
            action='revoke' if device['approved'] else 'approve'
            body+='<form method="post" action="'+action+'" style="margin-top:12px">'+csrf+'<input type="hidden" name="device" value="'+esc(key)+'"><button>'+('Freigabe entfernen' if device['approved'] else 'Diesen Kindle freigeben')+'</button></form></section>'
        if source:
            query=parse_qs(urlsplit(self.path).query);selected_key=query.get('preview',[''])[0]
            if selected_key not in config['devices']:selected_key=next(iter(config['devices']),'')
            size=query.get('size',['758'])[0];width,height=(600,800) if size=='600' else (758,1024)
            body+='<h2>Kindle-Vorschau</h2><form method="get" action="./"><label>Gerät <select name="preview">'
            for key,device in config['devices'].items():body+='<option value="'+esc(key)+'"'+(' selected' if key==selected_key else '')+'>'+esc(device.get('name') or 'Kindle '+device['code'])+'</option>'
            body+='</select></label><label>Vorschaugröße <select name="size"><option value="758"'+(' selected' if size!='600' else '')+'>758 × 1024</option><option value="600"'+(' selected' if size=='600' else '')+'>600 × 800</option></select></label><button>Vorschau aktualisieren</button></form>'
            body+='<div style="max-width:100%;overflow:auto;margin-top:16px"><iframe title="Kindle-Vorschau" src="preview?device='+esc(selected_key)+'" width="'+str(width)+'" height="'+str(height)+'" style="border:1px solid #aaa;display:block"></iframe></div>'
            for path,warnings in status['warnings'].items():
                if warnings:body+='<h3>Hinweise zu '+esc(path)+'</h3><ul>'+''.join('<li>'+esc(warning)+'</li>' for warning in warnings)+'</ul>'
            return page('Kindle Panel verwalten',body)
        # Offline/manual fallback stays available when no dashboard source was started.
        states=self.app.states()
        available=sorted([(entity,item) for entity,item in states.items() if valid_entity(entity)])
        body+='<h2>Manuelle Auswahl</h2><form method="post" action="save">'+csrf
        for index in range(8):
            selected=config['entities'][index] if index<len(config['entities']) else ''
            body+='<label>Kachel '+str(index+1)+'<select name="entity'+str(index)+'"><option value="">Leer</option>'
            for entity,item in available:
                body+='<option value="'+esc(entity)+'"'+(' selected' if entity==selected else '')+'>'+esc(item.get('attributes',{}).get('friendly_name',entity))+'</option>'
            body+='</select><input name="label'+str(index)+'" maxlength="60" value="'+esc(config.get('labels',{}).get(selected,''))+'"></label>'
        return page('Kindle Panel einrichten',body+'<button>Auswahl speichern</button></form>')

def make_server(app, address, admin=False, ingress_ip='172.30.32.2'):
    server = ThreadingHTTPServer(address, Handler)
    server.daemon_threads = True
    server.app = app
    server.admin = admin
    server.ingress_ip = ingress_ip
    return server

if __name__ == '__main__':
    app = App('/data')
    app.start_dashboard_source()
    ingress = make_server(app, ('0.0.0.0', 8099), admin=True)
    threading.Thread(target=ingress.serve_forever, daemon=True).start()
    print('Kindle Panel started: device port 8080, configuration through Home Assistant ingress', flush=True)
    make_server(app, ('0.0.0.0', 8080)).serve_forever()
