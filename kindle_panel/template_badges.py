"""Read-only Mushroom template badges; templates run only in Home Assistant."""
import hashlib
import json
import re
import threading
import time


def normalize(source, view_path, index, warn):
    if source.get('picture'):
        warn('Mushroom-Badge-Bilder werden noch nicht übersetzt.')
    for gesture in ('tap_action','hold_action','double_tap_action'):
        action=source.get(gesture,{})
        if isinstance(action,dict) and action.get('action','none')!='none':
            warn('Mushroom-Badge-Aktionen werden noch nicht übersetzt; Badge bleibt schreibgeschützt.')
    fields={}
    for key in ('content','label'):
        value=source.get(key,'')
        if not isinstance(value,str) or len(value)>8192:
            warn('Ungültiger Mushroom-Badge-Text.');return None
        fields[key]=value
    icon=source.get('icon','')
    if not isinstance(icon,str):icon=''
    if '{{' in icon or '{%' in icon:
        warn('Dynamische Mushroom-Badge-Icons werden noch nicht übersetzt.');icon='mdi:help-circle-outline'
    if icon.startswith('hass:'):icon='mdi:'+icon[5:]
    if not re.fullmatch(r'mdi:[a-z0-9-]+',icon):icon=''
    variables={key:source[key] for key in ('entity','area') if isinstance(source.get(key),str)}
    identity=hashlib.sha256(json.dumps([view_path,index,source],sort_keys=True).encode()).hexdigest()[:16]
    return {'type':'badge','template_id':'mushroom-'+identity,'templates':fields,'variables':variables,'icon':icon,'columns':3,'read_only':True}


def cards(config):
    return [card for group in config.get('dashboard_view',{}).get('groups',[]) for card in group['cards'] if card.get('template_id')]


class Renderer:
    def __init__(self, api, clock=time.monotonic):
        self.api=api;self.clock=clock;self.lock=threading.Lock();self.cache={}

    def values(self, config):
        result={}
        for card in cards(config):
            values={}
            for field,template in card['templates'].items():
                if not any(marker in template for marker in ('{{','{%','{#')):
                    values[field]=template;continue
                key=json.dumps([template,card['variables']],sort_keys=True)
                with self.lock:
                    now=self.clock();cached=self.cache.get(key)
                    if not cached or now-cached[0]>=10:
                        try:
                            text=self.api('template',{'template':template,'variables':card['variables']})
                            if not isinstance(text,str):raise ValueError('Template response is not text')
                            text=text[:1024]
                        except Exception:text='—'
                        cached=(now,text);self.cache[key]=cached
                        if len(self.cache)>256:self.cache={key:cached}
                    values[field]=cached[1]
            result[card['template_id']]=values
        return result
