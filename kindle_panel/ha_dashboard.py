"""Read a dedicated HA dashboard and translate a supported, non-executable subset."""
import copy
import hashlib
import json
import os
import re
import time

PATH = 'kindle-panel'
DOMAINS = {'sensor','binary_sensor','climate','light','switch','input_boolean','scene','weather','cover','script','fan'}
CONTROLS = {'climate','light','switch','input_boolean','scene','cover','script','fan'}


def commands(requests):
    # Import lazily so offline parser/tests need no network dependency.
    from websocket import create_connection
    token = os.environ.get('SUPERVISOR_TOKEN', '')
    if not token:
        raise RuntimeError('Home Assistant connection unavailable')
    ws = create_connection('ws://supervisor/core/websocket', timeout=10,
        http_no_proxy=['supervisor'], suppress_origin=True)
    try:
        if json.loads(ws.recv()).get('type') != 'auth_required':
            raise RuntimeError('Unexpected authentication handshake')
        ws.send(json.dumps({'type':'auth','access_token':token}))
        if json.loads(ws.recv()).get('type') != 'auth_ok':
            raise RuntimeError('Home Assistant authentication failed')
        results = []
        for number, request in enumerate(requests, 1):
            ws.send(json.dumps(dict(request, id=number)))
            while True:
                message = json.loads(ws.recv())
                if message.get('id') == number:
                    break
            if not message.get('success'):
                code = message.get('error',{}).get('code','unknown')
                raise RuntimeError('Dashboard command failed: ' + str(code))
            results.append(message.get('result'))
        return results
    finally:
        ws.close()


def valid_entity(value):
    return isinstance(value,str) and bool(re.fullmatch(r'[a-z_]+\.[a-z0-9_]+',value)) and value.split('.')[0] in DOMAINS


def default_columns(entity):
    domain=entity.split('.')[0]
    return 12 if domain=='climate' else 3 if domain in {'sensor','binary_sensor'} else 6


def seed(config):
    """Only used for a newly created dedicated dashboard; never overwrite an existing one."""
    cards=[]
    for entity in config.get('entities',[]):
        if not valid_entity(entity):continue
        climate=entity.startswith('climate.')
        card={'type':'thermostat' if climate else 'tile','entity':entity,
            'grid_options':{'columns':default_columns(entity),'rows':4 if climate else 2}}
        name=config.get('labels',{}).get(entity)
        if name:card['name']=name
        if climate:card['features']=[{'type':'climate-hvac-modes'}]
        cards.append(card)
    return {'views':[{'title':'Zuhause','path':'zuhause','type':'sections','max_columns':1,
        'sections':[{'type':'grid','cards':cards}]}]}


def ensure_dashboard(config, call=commands):
    dashboards=call([{'type':'lovelace/dashboards/list'}])[0]
    if not any(item.get('url_path')==PATH for item in dashboards):
        call([{'type':'lovelace/dashboards/create','title':'Kindle','url_path':PATH,
            'icon':'mdi:tablet','show_in_sidebar':True,'require_admin':False}])
        call([{'type':'lovelace/config/save','url_path':PATH,'config':seed(config)}])
    # Existing dashboards are read only, including empty configurations.
    return call([{'type':'lovelace/config','url_path':PATH}])[0]


def translate(raw, display=None):
    display=display or {}
    if not isinstance(raw,dict) or not isinstance(raw.get('views'),list):
        raise ValueError('Dashboard has no views')
    warnings=[]; views=[]; all_entities=[]; controls=[]
    def warn(message):
        if message not in warnings:warnings.append(message)
    for index,source in enumerate(raw['views']):
        if not isinstance(source,dict):continue
        if source.get('visible') is False or isinstance(source.get('visible'),(list,dict)):
            warn('Bedingt sichtbare Ansichten werden nicht angezeigt.');continue
        path=str(source.get('path',index)); title=str(source.get('title') or 'Seite '+str(index+1))
        groups=[]; seen=set()
        def parse_cards(cards, group_title='', forced_columns=None):
            output=[]
            if not isinstance(cards,list):return output
            for card in cards:
                if isinstance(card,str):card={'type':'entity','entity':card}
                if not isinstance(card,dict):continue
                if card.get('visibility'):
                    warn('Bedingte Karten werden zur Sicherheit nicht angezeigt.');continue
                kind=card.get('type','entity')
                if kind in {'grid','horizontal-stack','vertical-stack'}:
                    children=card.get('cards',[])
                    cols=card.get('columns',len(children) or 1) if kind!='vertical-stack' else 1
                    try:width=max(1,12//int(cols))
                    except (ValueError,TypeError,ZeroDivisionError):width=6
                    output.extend(parse_cards(children,forced_columns=width));continue
                if kind=='heading':
                    heading=str(card.get('heading',''))
                    if heading:output.append({'type':'heading','name':heading})
                    continue
                if kind=='entities':
                    output.extend(parse_cards(card.get('entities',[]),forced_columns=3));continue
                entity=card.get('entity')
                if kind not in {'tile','thermostat','entity','button','sensor'} or not valid_entity(entity):
                    warn('Nicht unterstützt: '+str(kind))
                    output.append({'type':'unsupported','name':str(card.get('title') or kind),'columns':12});continue
                if entity in seen:
                    warn('Doppelte Entität in „'+title+'“: '+entity);continue
                seen.add(entity)
                columns=card.get('grid_options',{}).get('columns',forced_columns or default_columns(entity))
                if columns=='full':columns=12
                try:columns=max(1,min(12,int(columns)))
                except (TypeError,ValueError):columns=default_columns(entity)
                if entity.startswith('climate.') and columns<6:
                    columns=6;warn('Klimapanels benötigen mindestens halbe Breite.')
                if entity.split('.')[0] in CONTROLS and not entity.startswith(('climate.','light.','script.','fan.','cover.')) and columns<6:
                    columns=6;warn('Bedienbare Kacheln benötigen mindestens halbe Breite.')
                action=card.get('tap_action',{}).get('action') if isinstance(card.get('tap_action',{}),dict) else None
                read_only=action=='none'
                if action not in (None,'none','more-info','toggle'):
                    read_only=True;warn('Spezielle Tipp-Aktion für '+entity+' wird nicht ausgeführt.')
                for feature in card.get('features',[]):
                    if isinstance(feature,dict) and feature.get('type') not in {'climate-hvac-modes','climate-temperature','toggle','cover-open-close'}:
                        warn('Zusatzbedienung '+str(feature.get('type'))+' wird noch nicht übersetzt.')
                name=card.get('name')
                if not isinstance(name,str):name=None
                icon=card.get('icon');icon=icon if isinstance(icon,str) and re.fullmatch(r'mdi:[a-z0-9-]+',icon) else None
                output.append({'type':'climate' if entity.startswith('climate.') else 'entity',
                    'entity':entity,'name':name,'icon':icon,'columns':columns,'read_only':read_only,
                    'width_set':'columns' in card.get('grid_options',{}) or forced_columns is not None,
                    'rows':card.get('grid_options',{}).get('rows')})
                if entity not in all_entities:all_entities.append(entity)
                if entity.split('.')[0] in CONTROLS and not read_only and entity not in controls:controls.append(entity)
            return output
        if source.get('type')=='sections' or 'sections' in source:
            for section in source.get('sections',[]):
                if not isinstance(section,dict):continue
                if section.get('visibility'):
                    warn('Bedingte Abschnitte werden zur Sicherheit nicht angezeigt.');continue
                groups.append({'title':str(section.get('title','')),'cards':parse_cards(section.get('cards',[]))})
        else:
            groups.append({'title':'','cards':parse_cards(source.get('cards',[]))})
        # Badges are stored on the view, outside cards/sections. Reuse the
        # incremental entity renderer; an existing card wins over a duplicate
        # badge so a status display cannot remove that card's controls.
        badges=[]
        raw_badges=source.get('badges',[])
        if not isinstance(raw_badges,list):
            warn('Ungültige Badge-Liste in „'+title+'“.');raw_badges=[]
        for badge in raw_badges:
            if isinstance(badge,str):badge={'type':'entity','entity':badge}
            if not isinstance(badge,dict):continue
            if badge.get('visibility') or badge.get('conditions') or badge.get('state_filter'):
                warn('Bedingte Badges werden zur Sicherheit nicht angezeigt.');continue
            if badge.get('type','entity')!='entity' or not valid_entity(badge.get('entity')):
                warn('Nicht unterstütztes Badge: '+str(badge.get('type','entity')));continue
            if badge.get('state_content','state') not in ('state',['state']):
                warn('Badge-Attribute werden noch nicht übersetzt: '+badge['entity']);continue
            normalized=dict(badge,type='entity',tap_action={'action':'none'},grid_options={'columns':3})
            for parsed in parse_cards([normalized]):
                parsed.update(type='badge',show_icon=badge.get('show_icon',True),show_state=badge.get('show_state',True))
                badges.append(parsed)
        if badges:groups.insert(0,{'title':'','cards':badges})
        views.append({'title':title,'path':path,'groups':groups})
    if not views:views=[{'title':'Zuhause','path':'zuhause','groups':[]}]
    selected_display={entity:display[entity] for entity in all_entities if entity in display}
    revision=hashlib.sha256(json.dumps([raw,selected_display,'four-column-stable-3'],sort_keys=True).encode()).hexdigest()
    return {'views':views,'entities':all_entities,'control_entities':controls,'warnings':warnings,'revision':revision,'display':selected_display}


def view_config(base, model, path=None):
    result=copy.deepcopy(base)
    view=next((view for view in model['views'] if view['path']==path),model['views'][0])
    cards=[card for group in view['groups'] for card in group['cards']]
    result.update(entities=[c['entity'] for c in cards if 'entity' in c],
        labels={c['entity']:c['name'] for c in cards if 'entity' in c and c.get('name')},
        icons={c['entity']:c.get('icon') or model.get('display',{}).get(c['entity'],{}).get('icon') for c in cards if 'entity' in c},
        display_precision={entity:entry['precision'] for entity,entry in model.get('display',{}).items() if 'precision' in entry},
        columns={c['entity']:c['columns'] for c in cards if 'entity' in c},
        read_only={c['entity']:c['read_only'] for c in cards if 'entity' in c},
        dashboard_view=view,dashboard_views=[{'path':v['path'],'title':v['title']} for v in model['views']],
        dashboard_revision=model['revision'])
    return result

class Source:
    """Cached dashboard models; never writes user dashboards after initial creation."""
    def __init__(self, call=commands):
        import threading
        self.call=call;self.lock=threading.RLock();self.models={};self.errors={};self.dashboards=[];self.display={};self.display_checked=None

    def refresh(self, seed_config, paths, bootstrap=False):
        listing=self.call([{'type':'lovelace/dashboards/list'}])[0]
        if bootstrap and not any(d.get('url_path')==PATH for d in listing):
            ensure_dashboard(seed_config,self.call)
            listing=self.call([{'type':'lovelace/dashboards/list'}])[0]
        if self.display_checked is None or time.monotonic()-self.display_checked>30:
            try:
                registry=self.call([{'type':'config/entity_registry/list_for_display'}])[0]
                display={}
                for entry in registry.get('entities',[]):
                    entity=entry.get('ei')
                    if not valid_entity(entity):continue
                    info={};precision=entry.get('dp');icon=entry.get('ic')
                    if isinstance(precision,int) and not isinstance(precision,bool) and 0<=precision<=20:info['precision']=precision
                    if isinstance(icon,str) and re.fullmatch(r'mdi:[a-z0-9-]+',icon):info['icon']=icon
                    if info:display[entity]=info
                with self.lock:self.display=display;self.display_checked=time.monotonic();self.errors.pop('entity_display',None)
            except Exception:
                with self.lock:self.errors['entity_display']='Anzeigeeinstellungen vorübergehend nicht erreichbar'
        with self.lock:self.dashboards=copy.deepcopy(listing);display=copy.deepcopy(self.display)
        for path in paths:
            try:
                raw=self.call([{'type':'lovelace/config','url_path':path}])[0]
                model=translate(raw,display)
                with self.lock:self.models[path]=model;self.errors.pop(path,None)
            except Exception as error:
                with self.lock:
                    self.errors[path]=str(error) if isinstance(error,(ValueError,RuntimeError)) else type(error).__name__
                    if 'config_not_found' in str(error):self.models.pop(path,None)

    def model(self,path):
        with self.lock:
            if path not in self.models:raise RuntimeError('Dashboard is not available')
            return copy.deepcopy(self.models[path])

    def status(self):
        with self.lock:
            return {'dashboards':copy.deepcopy(self.dashboards),'errors':dict(self.errors),
                'warnings':{path:list(model['warnings']) for path,model in self.models.items()}}
