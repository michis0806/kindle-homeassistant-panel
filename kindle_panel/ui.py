"""Monochrome HTML/CSS layouts compatible with the PW1's old WebKit."""
import html
import math
import re
from urllib.parse import urlencode
from icons import ICONS
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import time

MODES = {'off':'Aus', 'heat':'Heizen', 'cool':'Kühlen', 'heat_cool':'Heizen / Kühlen', 'fan_only':'Nur Lüften', 'dry':'Entfeuchten', 'auto':'Automatisch'}
KINDS = {'light':'Licht', 'switch':'Schalter', 'input_boolean':'Schalter', 'scene':'Szene', 'climate':'Raumklima', 'sensor':'Messwert', 'binary_sensor':'Status', 'weather':'Wetter','cover':'Abdeckung','script':'Skript','fan':'Lüfter'}
CSS = '''
*{-webkit-box-sizing:border-box;box-sizing:border-box}
body{margin:22px;background:#fff;color:#111;font:20px Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%}
html{width:100%;height:100%}body.kindle{width:100%;min-height:100%;padding:0;overflow-x:hidden}.kindle>.panel{width:100%;max-width:none;min-height:100%}
a{color:inherit}h1{font:normal 34px Georgia,serif;margin:0 0 16px}h2{font-size:23px}p{line-height:1.45}
button,input,select{font:inherit;color:#111;background:#fff;border:1px solid #777;border-radius:0;padding:12px}
button{cursor:pointer}button:disabled{color:#777;cursor:default}label{display:block;margin:18px 0}select{max-width:100%;width:100%}
.muted{font-size:16px;color:#555}.code{font-size:64px;letter-spacing:7px}body.kindle{margin:0}
.panel{max-width:860px;margin:0 auto}.masthead{padding:20px 22px 15px;border-bottom:2px solid #111}
.topline{font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#555;margin:0 0 7px}
.title-row{width:100%;border-collapse:collapse}.title-row td{padding:0;vertical-align:middle}.title-row h1{font:normal 36px Georgia,serif;margin:0;line-height:1.1}
.title-row .right{text-align:right;white-space:nowrap;width:64px}.refresh{display:inline-block;text-decoration:none;border:1px solid #111;padding:10px 13px;font-size:17px}
.exit-button{width:54px;height:48px;padding:7px 9px;line-height:1;border:1px solid #111}.exit-button svg{display:block;width:32px;height:32px}
.cards{width:100%;table-layout:fixed;border-collapse:separate;border-spacing:12px 0;margin:12px 0}.climate-row{margin:12px}.cards td.card.card-wide{width:100%}
.cards td.card{width:50%;height:178px;padding:14px 16px;border:1px solid #777;vertical-align:top}
.cards td.empty{border:0;background:none}.kind{font-size:12px;letter-spacing:1.6px;text-transform:uppercase;color:#555;margin:0 0 8px}
.card h2{font-size:22px;line-height:1.15;height:51px;margin:0;font-weight:normal;overflow:hidden;word-wrap:break-word}
.measure{font-size:42px;line-height:1.12;margin:10px 0 12px;font-weight:normal;white-space:nowrap}.measure .unit{font-size:22px;margin-left:4px}
.status{font-size:25px;line-height:1.2;margin:8px 0 13px}.status.unavailable{font-size:20px;color:#555}
.segment{width:100%;border-collapse:collapse;table-layout:fixed}.segment td{padding:0;width:50%}.segment form{margin:0}
.segment button{width:100%;padding:10px 0;border:1px solid #111;font-size:18px;line-height:1.1}
.segment td+td button{border-left:0}.segment button.active{background:#111;color:#fff}.segment button:disabled{color:#777;background:#fff;border-color:#999}
.climate-reading{font-size:32px;margin:6px 0 9px;line-height:1.2}.climate-reading small{font-size:16px;margin-left:8px;color:#555}.card .open{display:block;text-align:center;text-decoration:none;border:1px solid #111;padding:10px;font-size:18px}
.bottom{padding:5px 22px 18px}.bottom-table{width:100%;border-collapse:collapse;font-size:15px;color:#555}.bottom-table td{padding:0}.bottom-table .right{text-align:right}
.pager{display:inline-block;border:1px solid #111;text-decoration:none;padding:10px 14px;margin-left:8px;color:#111;font-size:17px}
.empty-state{padding:28px 24px;font-size:23px}.climate-main{padding:20px 22px}.back{font-size:17px;display:inline-block;margin-bottom:13px;text-decoration:none}
.climate-title{font:normal 31px Georgia,serif;line-height:1.2;margin:0 0 12px}.mode-badge{display:inline-block;border:1px solid #111;padding:6px 12px;font-size:16px}
.temperature-table{width:100%;border-collapse:collapse;margin:24px 0}.temperature-table td{vertical-align:middle;padding:0;text-align:center}
.temperature-table .step{width:68px}.temperature-table button{font-size:34px;width:60px;height:60px;line-height:1;border:1px solid #111;padding:0}
.target-label{font-size:13px;letter-spacing:1.6px;text-transform:uppercase;color:#555}.target{font:normal 59px Georgia,serif;line-height:1.1;margin:5px 0}.target small{font:21px Arial,sans-serif}
.current{font-size:18px;color:#555}.setting-row{border-top:1px solid #aaa;padding:17px 0}.setting-row h2{font-size:16px;letter-spacing:1px;text-transform:uppercase;font-weight:normal;margin:0 0 10px}
.apply-table{width:100%;border-collapse:collapse}.apply-table td{vertical-align:middle;padding:0}.apply-table .apply{width:116px;padding-left:10px}.apply-table select{width:100%;font-size:21px;padding:13px 9px;border:1px solid #777}.apply-table button{width:100%;font-size:18px;padding:15px 8px;border:1px solid #111;background:#111;color:#fff}
.climate-main .current{margin-bottom:8px}.climate-main form{margin:0}.notice{border:1px solid #777;padding:16px}.climate-foot{margin-top:12px;font-size:15px;color:#555}
@media(max-width:620px){.masthead{padding:15px 16px 12px}.title-row h1{font-size:31px}.cards{border-spacing:10px 0;margin:10px 0}.climate-row{margin:10px}.cards td.card{padding:12px;height:170px}.card h2{font-size:20px;height:46px}.measure{font-size:37px}.kind{font-size:11px}.segment button{font-size:17px}.bottom{padding-left:16px;padding-right:16px}.climate-main{padding:16px}}
.climate-panel{border:1px solid #777;padding:16px 16px 12px;margin:0;background:#fff;color:#111}
.climate-panel h2{font:normal 23px Arial,Helvetica,sans-serif;line-height:1.2;margin:0 0 4px;height:auto;overflow:visible;word-wrap:break-word}
.climate-panel .mode-status{text-align:center;font-size:17px;margin:4px 0 0}
.climate-panel .temperature-table{margin:6px 0 10px}.climate-panel .target{font:normal 56px Arial,Helvetica,sans-serif;margin:3px 0;white-space:nowrap}
.climate-panel .target small{font:21px Arial,sans-serif}.climate-panel .current{font-size:18px;margin:4px 0 0}
.climate-panel .temperature-table button{width:54px;height:54px;font:32px Arial,sans-serif;background:#fff;color:#111}
.mode-buttons{width:100%;table-layout:fixed;border-collapse:collapse;margin:0}.mode-buttons td{padding:0}.mode-buttons form{margin:0}
.mode-button{width:100%;height:50px;padding:10px 0;border:1px solid #111;background:#fff;color:#111;border-radius:0;line-height:1}
.mode-buttons td+td .mode-button{border-left:0}.mode-button svg{display:block;width:26px;height:26px;margin:0 auto}
.mode-button.active{background:#111;color:#fff}.mode-button:disabled{color:#999;border-color:#aaa;background:#fff}.mode-button.active:disabled{color:#ccc;background:#555}
.climate-more{display:block;text-align:right;font-size:14px;margin:6px 0 0}.cards td.climate-cell{padding:0;border:0;vertical-align:top}
.climate-detail .setting-row{margin-top:18px}.climate-detail .climate-foot{font-size:14px;line-height:1.4}
@media(max-width:620px){.climate-panel{padding:10px}.climate-panel h2{font-size:22px}.climate-panel .target{font-size:52px}.climate-panel .temperature-table .step{width:56px}.climate-panel .temperature-table button{width:50px;height:52px}.mode-button{height:50px;padding:10px 0}}

.dashboard .masthead{padding:10px 12px;border-bottom:1px solid #999}.dashboard .masthead .topline{display:none}
.dashboard .title-row{table-layout:fixed}.dashboard .title-row h1{font:normal 27px Arial,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dashboard-grid{width:100%;padding:4px;font-size:0;line-height:0}
.tile{display:inline-block;vertical-align:top;padding:4px;font-size:18px;line-height:1.2;overflow:hidden}
.tile-inner{height:116px;padding:10px;border:1px solid #aaa;border-radius:10px;background:#fff;color:#111;overflow:hidden}
.tile-heading{height:34px}.tile-icon{float:left;width:24px;height:24px;margin:3px 6px 0 0}.tile-icon svg{display:block;width:24px;height:24px}
.tile-label{font:normal 14px Arial,sans-serif;line-height:17px;height:34px;margin:0;overflow:hidden;word-wrap:break-word}
.tile-reading{font:normal 28px Arial,sans-serif;line-height:34px;margin:4px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tile-unit{display:block;font-size:13px;line-height:16px;min-height:16px;color:#555}.tile-status{font-size:18px;line-height:21px;white-space:normal;height:42px}
.tile-control{height:136px}.tile-control .tile-label{font-size:17px;line-height:19px;height:38px}.tile-control .tile-heading{height:38px}
.tile-control .tile-status{height:27px;margin:4px 0 5px}.tile-control .segment button{padding:8px 0;font-size:17px}
.tile-active{border-color:#111}.tile-unavailable{color:#777}.tile .climate-panel{border-radius:10px}
.badge-pill{display:inline-block;max-width:100%;height:44px;border:1px solid #aaa;border-radius:24px;padding:8px 11px;white-space:nowrap;overflow:hidden;vertical-align:top;font:18px/26px Arial,sans-serif}
.badge-icon{display:inline-block;width:24px;height:26px;vertical-align:top;margin-right:7px}.badge-icon svg{width:24px;height:24px;vertical-align:middle}.badge-unit{margin-left:4px}.badge-value{vertical-align:top}
.cover-inner{height:100px;padding:10px;border:1px solid #aaa;border-radius:10px;overflow:hidden}.cover-label{display:block;font:16px/22px Arial,sans-serif;height:22px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.cover-arrows{width:100%;table-layout:fixed;border-collapse:collapse;margin-top:8px}.cover-arrows td{padding:0 3px}.cover-arrows form{margin:0}.cover-arrows button{width:100%;height:48px;padding:0;font:30px/44px Arial,sans-serif;border-radius:6px}.cover-arrows button:disabled{color:#aaa;border-color:#ccc}
.light-form{margin:0}.light-button{display:block;width:100%;height:72px;padding:12px 10px;border:1px solid #aaa;border-radius:10px;text-align:left;background:#fff;color:#111;overflow:hidden}
.light-button.is-on{border-color:#111}.light-button:disabled{color:#999;border-color:#aaa}.light-button-icon{float:left;width:30px;height:40px;margin-right:8px;line-height:40px;text-align:center}
.light-button svg{width:28px;height:28px;vertical-align:middle}.light-button.is-on .light-slash{display:none}.light-button-label{display:block;height:40px;overflow:hidden;font:14px/40px Arial,sans-serif;white-space:nowrap;text-overflow:ellipsis}
.light-unknown{display:none}.light-button.is-unavailable svg{display:none}.light-button.is-unavailable .light-unknown{display:inline}
.tile-heading-card{font:normal 21px Arial,sans-serif;padding:5px 4px 0;line-height:28px}
.view-tabs{padding:6px 8px 0}.view-tab{display:inline-block;padding:9px 12px;margin:0 5px 4px 0;border:1px solid #777;border-radius:7px;text-decoration:none;font-size:16px}.view-tab.active{background:#111;color:#fff}
@media(max-width:620px){.dashboard .title-row h1{font-size:25px}.tile-inner{padding:9px}.tile-label{font-size:13px}.tile-reading{font-size:26px}.tile-control .tile-label{font-size:16px}}

'''

def esc(value):
    return html.escape(str(value), quote=True)

def number(value):
    if value is None:
        return '—'
    try:
        decimal=Decimal(str(value))
        if not decimal.is_finite(): return esc(value)
        return format(decimal.normalize(),'f').replace('.',',')
    except InvalidOperation:
        return esc(value)

def sensor_number(config,entity,value):
    precision=config.get('display_precision',{}).get(entity)
    if isinstance(precision,int) and not isinstance(precision,bool) and 0<=precision<=20:
        try:
            decimal=Decimal(str(value))
            if decimal.is_finite():
                with localcontext() as context:
                    context.prec=max(40,len(decimal.as_tuple().digits)+max(0,decimal.adjusted())+precision+2)
                    rounded=decimal.quantize(Decimal(1).scaleb(-precision),rounding=ROUND_HALF_UP)
                if rounded==0:rounded=abs(rounded)
                return format(rounded,'f').replace('.',',')
        except (InvalidOperation,ValueError):pass
    return number(value)

def label(config, entity, item):
    custom=config.get('labels',{}).get(entity)
    if custom:return custom
    name=item.get('attributes',{}).get('friendly_name',entity)
    if entity.startswith('climate.'):
        short=re.sub(r'\s+Klimaanlage(?:\s+Room\s+Temperature)?$', '', str(name), flags=re.I)
        return short or name
    return name

def hidden(device,entity,action=None):
    fields='<input type="hidden" name="csrf" value="'+esc(device['csrf'])+'"><input type="hidden" name="entity" value="'+esc(entity)+'">'
    if action: fields+='<input type="hidden" name="action" value="'+esc(action)+'">'
    return fields

# Icon: Pictogrammers Material Design Icons, Apache-2.0; see ICON-LICENSE.txt.
EXIT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="#111" d="M21.8,13H20V21H13V17.67L15.79,14.88L16.5,15C17.66,15 18.6,14.06 18.6,12.9C18.6,11.74 17.66,10.8 16.5,10.8A2.1,2.1 0 0,0 14.4,12.9L14.5,13.61L13,15.13V9.65C13.66,9.29 14.1,8.6 14.1,7.8A2.1,2.1 0 0,0 12,5.7A2.1,2.1 0 0,0 9.9,7.8C9.9,8.6 10.34,9.29 11,9.65V15.13L9.5,13.61L9.6,12.9A2.1,2.1 0 0,0 7.5,10.8A2.1,2.1 0 0,0 5.4,12.9A2.1,2.1 0 0,0 7.5,15L8.21,14.88L11,17.67V21H4V13H2.25C1.83,13 1.42,13 1.42,12.79C1.43,12.57 1.85,12.15 2.28,11.72L11,3C11.33,2.67 11.67,2.33 12,2.33C12.33,2.33 12.67,2.67 13,3L17,7V6H19V9L21.78,11.78C22.18,12.18 22.59,12.59 22.6,12.8C22.6,13 22.2,13 21.8,13M7.5,12A0.9,0.9 0 0,1 8.4,12.9A0.9,0.9 0 0,1 7.5,13.8A0.9,0.9 0 0,1 6.6,12.9A0.9,0.9 0 0,1 7.5,12M16.5,12C17,12 17.4,12.4 17.4,12.9C17.4,13.4 17,13.8 16.5,13.8A0.9,0.9 0 0,1 15.6,12.9A0.9,0.9 0 0,1 16.5,12M12,6.9C12.5,6.9 12.9,7.3 12.9,7.8C12.9,8.3 12.5,8.7 12,8.7C11.5,8.7 11.1,8.3 11.1,7.8C11.1,7.3 11.5,6.9 12,6.9Z"/><path d="M3 3L21 21" fill="none" stroke="#fff" stroke-width="4"/><path d="M3 3L21 21" fill="none" stroke="#111" stroke-width="2" stroke-linecap="round"/></svg>'

def exit_form(device):
    return '<form method="post" action="/kiosk-exit" style="margin:0"><input type="hidden" name="csrf" value="'+esc(device['csrf'])+'"><input type="hidden" name="controller" value="'+esc(device.get('controller_id',''))+'"><button class="exit-button" aria-label="Home Assistant verlassen" title="Home Assistant verlassen">'+EXIT_ICON+'</button></form>'

def masthead(title,refresh='./',eyebrow='Dein Zuhause',device=None):
    right=exit_form(device) if device else '<a class="refresh" href="'+esc(refresh)+'">Aktualisieren</a>'
    return '<header class="masthead"><div class="topline">'+esc(eyebrow)+'</div><table class="title-row"><tr><td><h1>'+esc(title)+'</h1></td><td class="right">'+right+'</td></tr></table></header>'


def display_state(domain,state,attrs):
    if state=='unknown':return 'Unbekannt'
    if state=='unavailable':return 'Nicht verfügbar'
    if domain=='climate':return MODES.get(state,esc(state))
    if domain=='binary_sensor' and attrs.get('device_class') in {'occupancy','motion','presence'}:
        names={'occupancy':('Belegt','Frei'),'motion':('Bewegung','Ruhig'),'presence':('Anwesend','Abwesend')}[attrs['device_class']]
        return {'on':names[0],'off':names[1]}.get(state,esc(state))
    if domain=='scene':return 'Bereit'
    if domain=='script':return 'Läuft' if state=='on' else 'Bereit'
    if domain=='cover':return {'open':'Offen','closed':'Geschlossen','opening':'Öffnet','closing':'Schließt'}.get(state,esc(state))
    if domain=='binary_sensor' and attrs.get('device_class') in {'door','window','opening','garage_door'}:
        return {'on':'Offen','off':'Geschlossen'}.get(state,esc(state))
    return {'on':'An','off':'Aus'}.get(state,esc(state))

def bid(entity, field):
    return 'e-' + entity.replace('.', '-') + '-' + field

def span(entity, field, value):
    return '<span id="'+bid(entity,field)+'">'+str(value)+'</span>'

MODE_ORDER = ('off','fan_only','dry','cool','heat','heat_cool','auto')
MODE_ICONS = {'off': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13"/></svg>', 'fan_only': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11M12.5,2C17,2 17.11,5.57 14.75,6.75C13.76,7.24 13.32,8.29 13.13,9.22C13.61,9.42 14.03,9.73 14.35,10.13C18.05,8.13 22.03,8.92 22.03,12.5C22.03,17 18.46,17.1 17.28,14.73C16.78,13.74 15.72,13.3 14.79,13.11C14.59,13.59 14.28,14 13.88,14.34C15.87,18.03 15.08,22 11.5,22C7,22 6.91,18.42 9.27,17.24C10.25,16.75 10.69,15.71 10.89,14.79C10.4,14.59 9.97,14.27 9.65,13.87C5.96,15.85 2,15.07 2,11.5C2,7 5.56,6.89 6.74,9.26C7.24,10.25 8.29,10.68 9.22,10.87C9.41,10.39 9.73,9.97 10.14,9.65C8.15,5.96 8.94,2 12.5,2Z"/></svg>', 'dry': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12,3.25C12,3.25 6,10 6,14C6,17.32 8.69,20 12,20A6,6 0 0,0 18,14C18,10 12,3.25 12,3.25M14.47,9.97L15.53,11.03L9.53,17.03L8.47,15.97M9.75,10A1.25,1.25 0 0,1 11,11.25A1.25,1.25 0 0,1 9.75,12.5A1.25,1.25 0 0,1 8.5,11.25A1.25,1.25 0 0,1 9.75,10M14.25,14.5A1.25,1.25 0 0,1 15.5,15.75A1.25,1.25 0 0,1 14.25,17A1.25,1.25 0 0,1 13,15.75A1.25,1.25 0 0,1 14.25,14.5Z"/></svg>', 'cool': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M20.79,13.95L18.46,14.57L16.46,13.44V10.56L18.46,9.43L20.79,10.05L21.31,8.12L19.54,7.65L20,5.88L18.07,5.36L17.45,7.69L15.45,8.82L13,7.38V5.12L14.71,3.41L13.29,2L12,3.29L10.71,2L9.29,3.41L11,5.12V7.38L8.5,8.82L6.5,7.69L5.92,5.36L4,5.88L4.47,7.65L2.7,8.12L3.22,10.05L5.55,9.43L7.55,10.56V13.45L5.55,14.58L3.22,13.96L2.7,15.89L4.47,16.36L4,18.12L5.93,18.64L6.55,16.31L8.55,15.18L11,16.62V18.88L9.29,20.59L10.71,22L12,20.71L13.29,22L14.7,20.59L13,18.88V16.62L15.5,15.17L17.5,16.3L18.12,18.63L20,18.12L19.53,16.35L21.3,15.88L20.79,13.95M9.5,10.56L12,9.11L14.5,10.56V13.44L12,14.89L9.5,13.44V10.56Z"/></svg>', 'heat': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M17.66 11.2C17.43 10.9 17.15 10.64 16.89 10.38C16.22 9.78 15.46 9.35 14.82 8.72C13.33 7.26 13 4.85 13.95 3C13 3.23 12.17 3.75 11.46 4.32C8.87 6.4 7.85 10.07 9.07 13.22C9.11 13.32 9.15 13.42 9.15 13.55C9.15 13.77 9 13.97 8.8 14.05C8.57 14.15 8.33 14.09 8.14 13.93C8.08 13.88 8.04 13.83 8 13.76C6.87 12.33 6.69 10.28 7.45 8.64C5.78 10 4.87 12.3 5 14.47C5.06 14.97 5.12 15.47 5.29 15.97C5.43 16.57 5.7 17.17 6 17.7C7.08 19.43 8.95 20.67 10.96 20.92C13.1 21.19 15.39 20.8 17.03 19.32C18.86 17.66 19.5 15 18.56 12.72L18.43 12.46C18.22 12 17.66 11.2 17.66 11.2M14.5 17.5C14.22 17.74 13.76 18 13.4 18.1C12.28 18.5 11.16 17.94 10.5 17.28C11.69 17 12.4 16.12 12.61 15.23C12.78 14.43 12.46 13.77 12.33 13C12.21 12.26 12.23 11.63 12.5 10.94C12.69 11.32 12.89 11.7 13.13 12C13.9 13 15.11 13.44 15.37 14.8C15.41 14.94 15.43 15.08 15.43 15.23C15.46 16.05 15.1 16.95 14.5 17.5H14.5Z"/></svg>', 'heat_cool': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12.92 1.58L11.18 2.58L12.39 4.67L11.8 6.85L9 7.6L7.38 6L7.42 3.59L5.43 3.59L5.43 5.42L3.59 5.42L3.6 7.42L6 7.42L7.65 9.03L6.9 11.82L4.68 12.4L2.59 11.2L1.59 12.93L3.17 13.84L2.26 15.42L4 16.42L5.19 14.33L7.42 13.75L7.92 14.26L9.32 12.86L8.78 12.32L9.53 9.54L12.32 8.78L12.85 9.32L14.26 7.91L13.73 7.37L14.32 5.19L16.41 4L15.41 2.25L13.83 3.16L12.92 1.58M20.72 4L4 20.72L5.27 22L10.16 17.11C10.63 17.43 11.15 17.68 11.71 17.83C14.38 18.55 17.12 16.96 17.83 14.29C18.22 12.86 17.93 11.36 17.11 10.16L22 5.27L20.72 4M18.74 9C19.18 9.63 19.53 10.38 19.75 11.19C19.97 12 20.03 12.81 19.96 13.61L22.65 10.41L18.74 9M19.32 15.95C19 16.67 18.5 17.35 17.93 17.94C17.34 18.53 16.66 19 15.96 19.34L20.05 20.06L19.32 15.95M9 18.71L10.41 22.66L13.59 19.95C12.81 20 12 19.97 11.19 19.76C10.36 19.54 9.62 19.17 9 18.71Z"/></svg>', 'auto': '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12,6V9L16,5L12,1V4A8,8 0 0,0 4,12C4,13.57 4.46,15.03 5.24,16.26L6.7,14.8C6.25,13.97 6,13 6,12A6,6 0 0,1 12,6M18.76,7.74L17.3,9.2C17.74,10.04 18,11 18,12A6,6 0 0,1 12,18V15L8,19L12,23V20A8,8 0 0,0 20,12C20,10.43 19.54,8.97 18.76,7.74Z"/></svg>'}

def climate_steps(item):
    attrs=item.get('attributes',{})
    try:
        target=Decimal(str(attrs['temperature'])); step=Decimal(str(attrs.get('target_temp_step',0.5)))
        minimum=Decimal(str(attrs['min_temp'])); maximum=Decimal(str(attrs['max_temp']))
        if not all(v.is_finite() for v in (target,step,minimum,maximum)) or step<=0: raise ValueError()
        return [(str(target-step),target-step<minimum),(str(target+step),target+step>maximum)]
    except (KeyError,InvalidOperation,ValueError,TypeError):
        return [('',True),('',True)]

def settings(item):
    attrs=item.get('attributes',{}); features=int(attrs.get('supported_features',0))
    return [('Betriebsart','climate_hvac',attrs.get('hvac_modes',[]),item['state'],MODES),
        ('Lüfter','climate_fan',attrs.get('fan_modes',[]) if features&8 else [],attrs.get('fan_mode'),
        {'auto':'Automatisch','quiet':'Leise','low':'Niedrig','medium':'Mittel','high':'Hoch'})]

def setting_name(value,names):
    return names.get(value,'Stufe '+str(value) if str(value).isdigit() else str(value))

def updates(config,states):
    patches=[]; confirmations={}
    def patch(entity,field,**values):
        patches.append(dict(id=bid(entity,field),**values))
    for entity in config['entities']:
        item=states.get(entity,{'state':'unavailable','attributes':{}}); attrs=item.get('attributes',{})
        state=item['state']; domain=entity.split('.')[0]; available=state not in {'unknown','unavailable'} or domain=='scene' and state=='unknown'
        writable=available and not config.get('read_only',{}).get(entity,False)
        plain=lambda value: html.unescape(str(value))
        patch(entity,'label',text=label(config,entity,item))
        patch(entity,'state',text=plain(display_state(domain,state,attrs)))
        if domain in {'light','fan'}:
            patch(entity,'toggle',value='turn_off' if state=='on' else 'turn_on',
                disabled=not writable or state not in {'on','off'},
                className='light-button '+('is-'+state if state in {'on','off'} else 'is-unavailable'),
                pressed=state=='on')
        for action in ('on','off','activate'):
            active=action==state
            patch(entity,action,disabled=not writable,className='active' if active else '')
        if domain=='script':patch(entity,'run',disabled=not writable or state=='on')
        if domain=='cover':
            for action,disabled in cover_actions(item):patch(entity,action,disabled=not writable or disabled)
        if domain=='sensor':
            patch(entity,'value',text=plain(sensor_number(config,entity,state) if available else display_state(domain,state,attrs)))
            patch(entity,'unit',text=str(attrs.get('unit_of_measurement','')) if available else '')
        if domain=='climate':
            for mode in MODE_ORDER:
                patch(entity,'mode-'+mode,disabled=not writable or mode not in attrs.get('hvac_modes',[]),className='mode-button'+(' active' if state==mode else ''))
            unit=attrs.get('temperature_unit','')
            patch(entity,'current',text=plain(number(attrs.get('current_temperature'))))
            patch(entity,'unit',text=unit)
            patch(entity,'target',text=plain(number(attrs.get('temperature'))))
            patch(entity,'target-unit',text=unit)
            patch(entity,'current-line',text='Aktuell '+plain(number(attrs.get('current_temperature')))+' '+unit)
            for field,(value,disabled) in zip(('minus','plus'),climate_steps(item)):
                patch(entity,field,value=value,disabled=disabled or not writable or not int(attrs.get('supported_features',0))&1)
            for title,action,values,current,names in settings(item):
                patch(entity,action,options=[{'value':str(v),'label':setting_name(v,names)} for v in values],value=str(current),disabled=not writable)
                patch(entity,action+'-apply',disabled=not writable or not values)
        confirmations[entity]={'state':state,'temperature':attrs.get('temperature'),'fan_mode':attrs.get('fan_mode')}
    return {'patches':patches,'entities':confirmations}

def live_footer():
    return '<span id="panel-status" role="status">Live-Verbindung wird gestartet …</span> · <a href="">Aktualisieren</a><noscript>JavaScript ist aus. Bitte manuell aktualisieren.</noscript>'

def default_columns(entity):
    domain=entity.split('.')[0]
    return 12 if domain=='climate' else 3 if domain in {'sensor','binary_sensor','light'} else 6

def dashboard_cards(config):
    if config.get('dashboard_view'):
        cards=[]
        for group in config['dashboard_view']['groups']:
            if group.get('title'):cards.append({'type':'heading','name':group['title']})
            cards.extend(group['cards'])
        return cards
    return [{'type':'climate' if entity.startswith('climate.') else 'entity','entity':entity,
        'columns':default_columns(entity),'read_only':False} for entity in config['entities']]

def card_columns(card):
    return 12 if card['type']=='heading' else card.get('columns',12)

def dashboard_pages(selected):
    cards=dashboard_cards({'entities':selected}) if not selected or isinstance(selected[0],str) else selected
    pages=[];current=[];height=0;row_width=0;row_height=0
    def card_height(card):
        if card['type']=='heading':return 38
        if card['type']=='badge':return 52
        if card['type']=='climate':return 270 if card_columns(card)<12 else 258
        if card.get('entity','').split('.')[0] in {'light','fan','script'} and not card.get('read_only'):return 80
        if card.get('entity','').startswith('cover.') and not card.get('read_only'):return 108
        return 144 if card.get('entity','').split('.')[0] in {'light','switch','input_boolean','scene'} else 124
    for index,card in enumerate(cards):
        if card['type']=='heading' and current and index+1<len(cards):
            following=cards[index+1]
            if height+(row_height if row_width else 0)+38+card_height(following)>620:
                pages.append(current);current=[];height=0;row_width=0;row_height=0
        if current and current[-1]['type']=='badge' and card['type']!='badge' and row_width:
            height+=row_height;row_width=0;row_height=0
        width=card_columns(card);cost=card_height(card)
        if row_width and row_width+width>12:
            height+=row_height;row_width=0;row_height=0
        needed=height+max(row_height,cost)
        if current and needed>620:
            pages.append(current);current=[];height=0;row_width=0;row_height=0
        current.append(card);row_width+=width;row_height=max(row_height,cost)
        if row_width>=12:
            height+=row_height;row_width=0;row_height=0
    if current:pages.append(current)
    return pages or [[]]

def entity_icon(config,entity,item):
    attrs=item.get('attributes',{});domain=entity.split('.')[0];device_class=attrs.get('device_class')
    default={'temperature':'thermometer','humidity':'water-percent','occupancy':'motion-sensor','motion':'motion-sensor',
        'presence':'account','door':'door','window':'window-closed','opening':'window-closed','power':'flash','energy':'flash','battery':'battery'}.get(device_class)
    if not default:default={'light':'lightbulb','switch':'power','input_boolean':'toggle-switch','scene':'home','cover':'window-shutter','script':'script-text-play','fan':'fan','weather':'cloud','climate':'radiator'}.get(domain,'gauge')
    name=config.get('icons',{}).get(entity) or attrs.get('icon') or 'mdi:'+default
    paths=ICONS.get(name,ICONS['mdi:'+default])
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">'+paths+'</svg>'

def badge_tile(config,card,entity,item):
    state=item['state'];attrs=item.get('attributes',{});domain=entity.split('.')[0]
    available=state not in {'unknown','unavailable'}
    body='<div class="badge-pill" title="'+esc(label(config,entity,item))+'">'
    if card.get('show_icon',True):body+='<span class="badge-icon">'+entity_icon(config,entity,item)+'</span>'
    if card.get('show_state',True):
        if domain=='sensor':
            body+='<span class="badge-value" id="'+bid(entity,'value')+'">'+(sensor_number(config,entity,state) if available else display_state(domain,state,attrs))+'</span><span class="badge-unit" id="'+bid(entity,'unit')+'">'+esc(attrs.get('unit_of_measurement','') if available else '')+'</span>'
        else:body+='<span class="badge-value" id="'+bid(entity,'state')+'">'+display_state(domain,state,attrs)+'</span>'
    return body+'</div>'

def light_button(config,entity,item,device,page_index):
    state=item['state'];known=state in {'on','off'}
    path=ICONS['mdi:fan'] if entity.startswith('fan.') else ICONS['mdi:lightbulb']
    icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">'+path+'<g class="light-slash"><path d="M3 3L21 21" fill="none" stroke="#fff" stroke-width="4"/><path d="M3 3L21 21" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></g></svg>'
    return ('<form class="light-form" method="post" action="action">'+hidden(device,entity)+
        '<input type="hidden" name="seite" value="'+str(page_index)+'">'+
        '<button id="'+bid(entity,'toggle')+'" class="light-button '+('is-'+state if known else 'is-unavailable')+
        '" name="action" value="'+('turn_off' if state=='on' else 'turn_on')+'" aria-pressed="'+('true' if state=='on' else 'false')+'"'+(' disabled' if not known else '')+'>'+
        '<span class="light-button-icon">'+icon+'<span class="light-unknown" aria-hidden="true">?</span></span>'+
        '<span class="light-button-label" id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</span></button></form>')

def cover_actions(item):
    attrs=item.get('attributes',{});features=int(attrs.get('supported_features',0));position=attrs.get('current_position');state=item['state']
    return [('open_cover',not features&1 or state=='opening' or position==100),
        ('close_cover',not features&2 or state in {'closing','closed'} or position==0)]

def cover_tile(entity,item,device,page_index,config):
    body='<div class="cover-inner"><span class="cover-label" id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</span><table class="cover-arrows"><tr>'
    for action,disabled in cover_actions(item):
        body+='<td><form method="post" action="action">'+hidden(device,entity,action)+'<input type="hidden" name="seite" value="'+str(page_index)+'"><button id="'+bid(entity,action)+'" aria-label="'+('Öffnen' if action=='open_cover' else 'Schließen')+'"'+(' disabled' if disabled or item['state'] in {'unknown','unavailable'} else '')+'>'+('↑' if action=='open_cover' else '↓')+'</button></form></td>'
    return body+'</tr></table></div>'

def script_tile(config,entity,item,device,page_index):
    return ('<form class="light-form" method="post" action="action">'+hidden(device,entity,'activate')+
        '<input type="hidden" name="seite" value="'+str(page_index)+'"><button class="light-button" id="'+bid(entity,'run')+'"'+(' disabled' if item['state'] in {'on','unknown','unavailable'} else '')+'>'+
        '<span class="light-button-icon">'+entity_icon(config,entity,item)+'</span><span class="light-button-label" id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</span></button></form>')

def tile(config,card,states,device,page_index):
    columns=card_columns(card);width=columns*100/12
    start=('<div class="tile badge-slot" style="width:auto">' if card['type']=='badge' else '<div class="tile" style="width:'+format(width,'.5f')+'%">')
    if card['type']=='heading':return start+'<div class="tile-heading-card">'+esc(card.get('name',''))+'</div></div>'
    if card['type']=='unsupported':return start+'<div class="tile-inner"><h2 class="tile-label">'+esc(card['name'])+'</h2><p>Diese Karte wird noch nicht unterstützt.</p></div></div>'
    entity=card['entity'];item=states.get(entity,{'state':'unavailable','attributes':{}});attrs=item.get('attributes',{});state=item['state'];domain=entity.split('.')[0]
    if card['type']=='badge':return start+badge_tile(config,card,entity,item)+'</div>'
    if domain=='climate':return start+climate_panel(config,entity,item,device,more=True)+'</div>'
    if domain in {'light','fan'} and not card.get('read_only',False):return start+light_button(config,entity,item,device,page_index)+'</div>'
    if domain=='cover' and not card.get('read_only',False):return start+cover_tile(entity,item,device,page_index,config)+'</div>'
    if domain=='script' and not card.get('read_only',False):return start+script_tile(config,entity,item,device,page_index)+'</div>'
    control=domain in {'light','switch','input_boolean','scene'} and not card.get('read_only',False)
    unavailable=state=='unavailable' or state=='unknown' and domain!='scene'
    body=start+'<div class="tile-inner'+(' tile-control' if control else '')+'"><div class="tile-heading"><span class="tile-icon">'+entity_icon(config,entity,item)+'</span><h2 class="tile-label" id="'+bid(entity,'label')+'" title="'+esc(label(config,entity,item))+'">'+esc(label(config,entity,item))+'</h2></div>'
    if domain=='sensor':
        body+='<div class="tile-reading" id="'+bid(entity,'value')+'">'+(display_state(domain,state,attrs) if unavailable else sensor_number(config,entity,state))+'</div><span class="tile-unit" id="'+bid(entity,'unit')+'">'+esc(attrs.get('unit_of_measurement','') if not unavailable else '')+'</span>'
    else:
        body+='<div class="tile-reading tile-status" id="'+bid(entity,'state')+'">'+display_state(domain,state,attrs)+'</div>'
    if control:
        actions=[('An','turn_on','on'),('Aus','turn_off','off')] if domain!='scene' else [('Starten','activate','activate')]
        body+='<table class="segment"><tr>'
        for text,action,field in actions:
            body+='<td><form method="post" action="action">'+hidden(device,entity)+'<input type="hidden" name="seite" value="'+str(page_index)+'"><button id="'+bid(entity,field)+'" name="action" value="'+action+'"'+(' class="active"' if field==state else '')+(' disabled' if unavailable else '')+'>'+text+'</button></form></td>'
        body+='</tr></table>'
    return body+'</div></div>'

def dashboard(config,states,device,page_index,refresh):
    groups=dashboard_pages(dashboard_cards(config));pages=len(groups);page_index=max(0,min(pages-1,page_index))
    view=config.get('dashboard_view',{});view_path=view.get('path');title=view.get('title','Zuhause')
    query=lambda index:'?'+urlencode(dict({'seite':index},**({'view':view_path} if view_path else {})))
    body='<div class="panel dashboard" id="dashboard-root" data-revision="'+esc(config.get('dashboard_revision',''))+'">'+masthead(title,query(page_index),device=device)
    views=config.get('dashboard_views',[])
    if len(views)>1:
        body+='<nav class="view-tabs">'
        for item in views:body+='<a class="view-tab'+(' active' if item['path']==view_path else '')+'" href="?'+urlencode({'view':item['path']})+'">'+esc(item['title'])+'</a>'
        body+='</nav>'
    if not any(groups):
        body+='<div class="empty-state">Dieses Dashboard ist noch leer.</div>'
    body+='<div class="dashboard-grid">';in_badges=False
    for card in groups[page_index]:
        badge=card['type']=='badge'
        if in_badges and not badge:body+='</div>';in_badges=False
        if badge and not in_badges:body+='<div class="dashboard-badges">';in_badges=True
        body+=tile(config,card,states,device,page_index)
    if in_badges:body+='</div>'
    body+='</div>'
    body+='<footer class="bottom"><table class="bottom-table"><tr><td>'+live_footer()+'</td><td class="right">'
    if pages>1:
        body+=str(page_index+1)+' / '+str(pages)
        if page_index:body+='<a class="pager" href="'+query(page_index-1)+'">Zurück</a>'
        if page_index+1<pages:body+='<a class="pager" href="'+query(page_index+1)+'">Weiter</a>'
    return body+'</td></tr></table></footer></div><script src="/panel.js"></script>'

def climate_panel(config,entity,item,device,more=False):
    attrs=item.get('attributes',{});unit=attrs.get('temperature_unit','');state=item['state'];available=state not in {'unknown','unavailable'} and not config.get('read_only',{}).get(entity,False)
    body='<div class="climate-panel"><h2 id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</h2><div class="mode-status" id="'+bid(entity,'state')+'">'+display_state('climate',state,attrs)+'</div>'
    if int(attrs.get('supported_features',0))&1:
        steps=climate_steps(item)
        body+='<table class="temperature-table"><tr>'
        for field in ('minus','target','plus'):
            if field=='target':
                body+='<td><div class="target">'+span(entity,'target',number(attrs.get('temperature')))+'<small> '+span(entity,'target-unit',esc(unit))+'</small></div><div class="current" id="'+bid(entity,'current-line')+'">Aktuell '+number(attrs.get('current_temperature'))+' '+esc(unit)+'</div></td>'
            else:
                value,disabled=steps[0 if field=='minus' else 1]
                body+='<td class="step"><form method="post" action="action">'+hidden(device,entity,'climate_temperature')+'<button id="'+bid(entity,field)+'" name="value" value="'+esc(value)+'" aria-label="'+('Solltemperatur senken' if field=='minus' else 'Solltemperatur erhöhen')+'"'+(' disabled' if disabled or not available else '')+'>'+('−' if field=='minus' else '+')+'</button></form></td>'
        body+='</tr></table>'
    else:
        body+='<p class="current" id="'+bid(entity,'current-line')+'">Aktuell '+number(attrs.get('current_temperature'))+' '+esc(unit)+'</p>'
    modes=[mode for mode in MODE_ORDER if mode in attrs.get('hvac_modes',[])]
    if modes:
        body+='<table class="mode-buttons"><tr>'
        for mode in modes:
            body+='<td><form method="post" action="action">'+hidden(device,entity,'climate_hvac')+'<button id="'+bid(entity,'mode-'+mode)+'" class="mode-button'+(' active' if state==mode else '')+'" name="value" value="'+mode+'" title="'+esc(MODES[mode])+'" aria-label="'+esc(MODES[mode])+'"'+(' disabled' if not available else '')+'>'+MODE_ICONS[mode]+'</button></form></td>'
        body+='</tr></table>'
    if more:
        body+='<a class="climate-more" href="?klima='+esc(entity)+'">Weitere Einstellungen ›</a>'
    return body+'</div>'

def climate(config,entity,item,device):
    attrs=item.get('attributes',{});available=item['state'] not in {'unknown','unavailable'} and not config.get('read_only',{}).get(entity,False)
    body='<div class="panel"><div class="climate-main climate-detail"><div style="float:right">'+exit_form(device)+'</div><a class="back" href="./">‹ Übersicht</a><div style="clear:both"></div>'+climate_panel(config,entity,item,device)
    for title,action,values,current,names in settings(item):
        if action=='climate_hvac' or not values:continue
        body+='<section class="setting-row"><h2>'+title+'</h2><form method="post" action="action">'+hidden(device,entity,action)+'<table class="apply-table"><tr><td><select id="'+bid(entity,action)+'" name="value"'+(' disabled' if not available else '')+'>'
        for value in values:
            body+='<option value="'+esc(value)+'"'+(' selected' if value==current else '')+'>'+esc(setting_name(value,names))+'</option>'
        body+='</select></td><td class="apply"><button id="'+bid(entity,action+'-apply')+'"'+(' disabled' if not available else '')+'>Setzen</button></td></tr></table></form></section>'
    return body+'<p class="climate-foot">−/+ ändert nur die Solltemperatur. Die Symbole darunter setzen direkt die Betriebsart.</p><p class="climate-foot">'+live_footer()+'</p></div></div><script src="/panel.js"></script>'
