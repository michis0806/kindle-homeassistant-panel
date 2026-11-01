"""Monochrome HTML/CSS layouts compatible with the PW1's old WebKit."""
import html
import math
import re
from urllib.parse import urlencode, urlsplit, unquote
from icons import ICONS
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import time
import template_badges

MODES = {'off':'Aus', 'heat':'Heizen', 'cool':'Kühlen', 'heat_cool':'Heizen / Kühlen', 'fan_only':'Nur Lüften', 'dry':'Entfeuchten', 'auto':'Automatisch'}
KINDS = {'light':'Licht', 'switch':'Schalter', 'input_boolean':'Schalter', 'scene':'Szene', 'climate':'Raumklima', 'sensor':'Messwert', 'binary_sensor':'Status', 'weather':'Wetter','cover':'Abdeckung','script':'Skript','fan':'Lüfter'}
CSS = '''
*{-webkit-box-sizing:border-box;box-sizing:border-box}
body{margin:22px;background:#fff;color:#111;font:20px Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%}
html{width:100%;height:100%;overflow-x:hidden}body.kindle{width:100%;min-height:100%;padding:0;overflow-x:hidden}.kindle>.panel{width:100%;max-width:100%;min-height:100%;overflow:hidden}
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
.badge-icon{display:inline-block;width:24px;height:26px;vertical-align:top;margin-right:7px}.badge-icon svg{width:24px;height:24px;vertical-align:middle}.badge-caption{margin-left:6px;font-size:13px;color:#555}.badge-caption:empty{display:none}.badge-unit{margin-left:4px}.badge-value{vertical-align:top}
.cover-inner{height:100px;padding:10px;border:1px solid #aaa;border-radius:10px;overflow:hidden}.cover-label{display:block;font:16px/22px Arial,sans-serif;height:22px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.cover-arrows{width:100%;table-layout:fixed;border-collapse:collapse;margin-top:8px}.cover-arrows td{padding:0 3px}.cover-arrows form{margin:0}.cover-arrows button{width:100%;height:48px;padding:0;font:30px/44px Arial,sans-serif;border-radius:6px}.cover-arrows button:disabled{color:#aaa;border-color:#ccc}
.entity-link{color:inherit;text-decoration:none}.action-link{display:block;text-decoration:none}.light-form{margin:0}.light-button{display:block;width:100%;height:72px;padding:12px 10px;border:1px solid #aaa;border-radius:10px;text-align:left;background:#fff;color:#111;overflow:hidden}
.light-button.is-on{border-color:#111}.light-button:disabled{color:#999;border-color:#aaa}.light-button-icon{float:left;width:30px;height:40px;margin-right:8px;line-height:40px;text-align:center}
.light-button svg{width:28px;height:28px;vertical-align:middle}.light-button.is-on .light-slash{display:none}.light-button-label{display:block;height:40px;overflow:hidden;font:14px/40px Arial,sans-serif;white-space:nowrap;text-overflow:ellipsis}
.light-unknown{display:none}.light-button.is-unavailable svg{display:none}.light-button.is-unavailable .light-unknown{display:inline}
.tile-heading-card{font:normal 21px Arial,sans-serif;padding:5px 4px 0;line-height:28px}
.view-tabs{padding:6px 8px 0}.view-tab{display:inline-block;padding:9px 12px;margin:0 5px 4px 0;border:1px solid #777;border-radius:7px;text-decoration:none;font-size:16px}.view-tab.active{background:#111;color:#fff}
@media(max-width:620px){.dashboard .title-row h1{font-size:25px}.tile-inner{padding:9px}.tile-label{font-size:13px}.tile-reading{font-size:26px}.tile-control .tile-label{font-size:16px}}

.pagination{height:48px;white-space:nowrap;text-align:center;margin-top:4px;overflow:hidden}.pagination .pager{font-size:15px;padding:8px 12px;margin:0;vertical-align:middle}.pagination .pager[aria-disabled]{color:#aaa;border-color:#ccc}.page-count{display:inline-block;min-width:64px;text-align:center;font-size:14px;vertical-align:middle}.live-line{font-size:12px;line-height:18px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.climate-heading{position:relative;padding-right:30px}.climate-info{position:absolute;right:0;top:0;width:28px;height:28px;text-align:center;font:24px/28px Arial,sans-serif;text-decoration:none}.four-grid{position:relative;width:100%}.grid-card{position:absolute;overflow:hidden}.tile-cell{display:block}.dashboard-grid{padding:2px}
.dashboard .masthead{padding:6px 8px}.dashboard .title-row h1{font-size:23px}.dashboard .exit-button{height:44px;width:46px;padding:6px}.dashboard .exit-button svg{height:28px;width:28px}
.dashboard .climate-panel{height:200px;padding:8px}.dashboard .climate-panel h2{font-size:20px;line-height:24px}.dashboard .climate-panel .mode-status{font-size:15px}.dashboard .climate-panel .target{font-size:36px}.dashboard .climate-panel .current{font-size:15px}
.dashboard .climate-panel .temperature-table{table-layout:fixed;margin:4px 0}.dashboard .climate-panel .temperature-table .step{width:50px}.dashboard .climate-panel .temperature-table button{width:44px;height:48px;font-size:28px}
.dashboard .mode-button{height:40px;padding:6px 0}.dashboard .mode-button svg{height:24px;width:24px}.dashboard .climate-more{font-size:12px;margin-top:4px}
.dashboard .cover-inner{height:96px;padding:6px}.dashboard .cover-label{height:20px;font-size:15px;line-height:20px;white-space:nowrap;text-overflow:ellipsis}.cover-state{display:block;height:14px;font-size:12px;line-height:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#555}.dashboard .cover-arrows{margin-top:4px}.dashboard .cover-arrows td{padding:0 2px}.dashboard .cover-arrows button{height:40px;font-size:26px;line-height:36px}
.dashboard .light-button{height:44px;padding:3px 8px}.dashboard .light-button-icon{width:26px;height:36px;line-height:36px;margin-right:6px}.dashboard .light-button svg{width:24px;height:24px}.dashboard .light-button-label{height:36px;font-size:15px;line-height:36px;white-space:nowrap;text-overflow:ellipsis}
.dashboard .tile-inner{height:96px;padding:6px}.dashboard .tile-control{height:148px}.dashboard .tile-heading{height:28px}.dashboard .tile-label{height:28px;line-height:14px}.dashboard .tile-unit{font-size:12px;line-height:14px}.dashboard .tile-reading{margin-top:2px}.dashboard .tile-label{font-size:13px}.dashboard .tile-reading{font-size:24px;line-height:28px}.dashboard .tile-status{font-size:17px;line-height:20px}
.dashboard .tile-heading-card{font-size:18px;line-height:24px;padding:2px 4px}.side-heading{font-size:15px;line-height:20px;padding:2px 4px}.dashboard .bottom{padding:4px 8px 8px}.dashboard .bottom-table{font-size:12px}


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
    if device.get('view'):fields+='<input type="hidden" name="view" value="'+esc(device['view'])+'">'
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

def climate_modes(config,entity,attrs):
    supported=attrs.get('hvac_modes',[])
    if not isinstance(supported,list):supported=[]
    allowed=config.get('climate_modes',{}).get(entity)
    return [mode for mode in MODE_ORDER if mode in supported and (allowed is None or mode in allowed)]

def setting_name(value,names):
    return names.get(value,'Stufe '+str(value) if str(value).isdigit() else str(value))

def updates(config,states):
    patches=[]; confirmations={}
    for card in template_badges.cards(config):
        values=config.get('template_values',{}).get(card['template_id'],{})
        for field in ('content','label'):
            patches.append({'id':'t-'+card['template_id']+'-'+field,'text':values.get(field,'—' if field=='content' else '')})
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
            patch(entity,'cover-status',text=plain(cover_status(item)))
            for action,disabled in cover_actions(item):patch(entity,action,disabled=not writable or disabled)
        if domain=='sensor':
            patch(entity,'value',text=plain(sensor_number(config,entity,state) if available else display_state(domain,state,attrs)))
            patch(entity,'unit',text=str(attrs.get('unit_of_measurement','')) if available else '')
        if domain=='climate':
            allowed_modes=climate_modes(config,entity,attrs)
            for mode in MODE_ORDER:
                patch(entity,'mode-'+mode,disabled=not writable or mode not in allowed_modes,className='mode-button'+(' active' if state==mode else ''))
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
        for index,group in enumerate(config['dashboard_view']['groups']):
            if index:cards.append({'type':'section-break'})
            if group.get('title'):cards.append({'type':'heading','name':group['title']})
            cards.extend(group['cards'])
        return cards
    return [{'type':'climate' if entity.startswith('climate.') else 'entity','entity':entity,
        'columns':default_columns(entity),'read_only':False} for entity in config['entities']]

def card_columns(card):
    return 12 if card['type']=='heading' else card.get('columns',12)

GRID_UNIT=52

def compact_span(card):
    if card['type']=='heading':return 4
    return max(1,min(4,math.ceil(card_columns(card)/3)))

def card_units(card):
    domain=card.get('entity','').split('.')[0]
    linked=card.get('actions',{}).get('tap',{}).get('kind') in {'more-info','navigate','url'}
    minimum=1 if linked and domain not in {'cover','climate'} else 3 if domain=='climate' else 1 if domain in {'light','fan','script'} and not card.get('read_only') else 3 if domain in {'switch','input_boolean','scene'} and not card.get('read_only') else 2
    rows=card.get('rows')
    return max(minimum,min(12,rows)) if isinstance(rows,int) and not isinstance(rows,bool) else minimum

def place_cards(cards):
    occupied=[];placements=[]
    for card in cards:
        span=compact_span(card);units=card_units(card);row=0;found=False
        while not found:
            while len(occupied)<row+units:occupied.append([False]*4)
            for column in range(5-span):
                if all(not occupied[r][c] for r in range(row,row+units) for c in range(column,column+span)):
                    for r in range(row,row+units):
                        for c in range(column,column+span):occupied[r][c]=True
                    placements.append({'card':card,'row':row,'column':column,'span':span,'units':units})
                    found=True;break
            if not found:row+=1
    rows=max((p['row']+p['units'] for p in placements),default=0)
    return placements,rows

def layout_blocks(selected):
    cards=dashboard_cards({'entities':selected}) if not selected or isinstance(selected[0],str) else selected
    blocks=[];pending=[]
    def flush():
        if pending:
            placed,rows=place_cards(pending)
            blocks.append({'kind':'grid','cards':list(pending),'placements':placed,'rows':rows,'height':rows*GRID_UNIT})
            pending.clear()
    badges=[c for c in cards if c['type']=='badge']
    if badges:blocks.append({'kind':'badges','cards':badges,'height':52*math.ceil(len(badges)/4)})
    for card in cards:
        if card['type']=='badge':continue
        if card['type'] in {'heading','section-break'}:
            flush()
            if card['type']=='heading':blocks.append({'kind':'heading','cards':[card],'height':28})
        else:pending.append(card)
    flush()
    return blocks

def dashboard_layout_pages(selected):
    blocks=layout_blocks(selected);pages=[];page=[];height=0
    # Multipage views reserve room for the navigation before laying out cards.
    budget=620 if sum(block['height'] for block in blocks)<=620 else 520
    for index,block in enumerate(blocks):
        reserve=blocks[index+1]['height'] if block['kind']=='heading' and index+1<len(blocks) else 0
        if page and height+block['height']+reserve>budget and not (block['kind']=='grid' and block['height']>budget):
            pages.append(page);page=[];height=0
        # Split large sections on complete visual row boundaries. Cards spanning
        # several rows remain together so their controls are never cut apart.
        if block['kind']=='grid' and block['height']>budget:
            boundaries=[row for row in range(1,block['rows']+1) if not any(p['row']<row<p['row']+p['units'] for p in block['placements'])]
            start_row=0
            while start_row<block['rows']:
                capacity=max(0,(budget-height)//GRID_UNIT)
                candidates=[row for row in boundaries if start_row<row<=start_row+capacity]
                if not candidates and page:
                    pages.append(page);page=[];height=0
                    candidates=[row for row in boundaries if start_row<row<=start_row+budget//GRID_UNIT]
                end=max(candidates) if candidates else next(row for row in boundaries if row>start_row)
                chosen=[dict(p,row=p['row']-start_row) for p in block['placements'] if start_row<=p['row']<end]
                part=dict(block,placements=chosen,cards=[p['card'] for p in chosen],rows=end-start_row,height=(end-start_row)*GRID_UNIT)
                if page and height+part['height']>budget:pages.append(page);page=[];height=0
                page.append(part);height+=part['height'];start_row=end
                if start_row<block['rows']:pages.append(page);page=[];height=0
        else:page.append(block);height+=block['height']
    if page:pages.append(page)
    return pages or [[]]

def dashboard_pages(selected):
    return [[card for block in page for card in block['cards']] for page in dashboard_layout_pages(selected)]

def layout_css(blocks):
    maximum=max((block.get('rows',0) for block in blocks),default=1)
    rules=[]
    for unit in (52,60,68,80):
        prefix='#dashboard-root.layout-u'+str(unit)
        def rule(selector,values):
            rules.append(prefix+' '+selector+'{'+(';'.join(key+':'+str(value) for key,value in values.items()))+'}')
        px=lambda value:str(value)+'px'
        for row in range(maximum+1):
            rule('.grid-y-'+str(row),{'top':px(row*unit)})
            rule('.grid-h-'+str(row),{'height':px(row*unit)})
            if row:
                for selector in ('.climate-panel','.cover-inner','.light-button','.tile-inner'):
                    rule('.grid-n-'+str(row)+' '+selector,{'height':px((min(row,3) if selector=='.climate-panel' else row)*unit-8)})
        if unit==52:continue
        big=unit==80;middle=unit==68
        font=18 if big else 17 if middle else 16
        button=unit-8;label=button-22
        rule('.light-button',{'padding':'10px 12px'})
        rule('.light-button-icon',{'width':'34px','height':px(label),'line-height':px(label),'margin-right':'10px'})
        rule('.light-button svg',{'width':'30px','height':'30px'})
        rule('.light-button-label',{'height':px(label),'font-size':px(font),'line-height':px(label)})
        cover_label=26 if big else 24 if middle else 22
        cover_state=20 if big else 18 if middle else 16
        cover_margin=8 if big else 6 if middle else 4
        cover_button=72 if big else 56 if middle else 46
        rule('.cover-inner',{'padding':'10px'})
        rule('.cover-label',{'height':px(cover_label),'font-size':px(font),'line-height':px(cover_label)})
        rule('.cover-state',{'height':px(cover_state),'font-size':px(15 if big else 14 if middle else 13),'line-height':px(cover_state)})
        rule('.cover-arrows',{'margin-top':px(cover_margin)})
        rule('.cover-arrows button',{'height':px(cover_button),'font-size':'32px','line-height':px(cover_button-4)})
        target=48 if big else 46 if middle else 42
        step=60 if big else 56 if middle else 50
        mode=64 if big else 52 if middle else 46
        rule('.climate-panel',{'padding':'10px'})
        rule('.climate-panel h2',{'font-size':px(24 if big else 22 if middle else 20),'line-height':px(28 if big else 26 if middle else 24)})
        rule('.climate-panel .mode-status',{'font-size':px(17 if big else 16 if middle else 15),'margin':('4px 0 0' if big else '2px 0 0')})
        rule('.climate-panel .target',{'font-size':px(target),'margin':('3px 0' if big else '2px 0')})
        rule('.climate-panel .current',{'font-size':px(18 if big else 17 if middle else 16)})
        rule('.climate-panel .temperature-table',{'margin':('8px 0' if big else '6px 0' if middle else '4px 0')})
        rule('.climate-panel .temperature-table .step',{'width':px(step+4)})
        rule('.climate-panel .temperature-table button',{'width':px(step),'height':px(step),'font-size':'34px'})
        rule('.mode-button',{'height':px(mode),'padding':str(min(10,(mode-30)//2))+'px 0'})
        rule('.mode-button svg',{'height':'28px','width':'28px'})
        rule('.climate-more',{'font-size':px(14 if big else 13 if middle else 12),'margin-top':px(6 if big else 5 if middle else 4)})
        heading=40 if big else 36 if middle else 32
        rule('.tile-inner',{'padding':'8px'})
        rule('.tile-label',{'font-size':px(18 if big else 16 if middle else 15),'line-height':px(heading//2),'height':px(heading)})
        rule('.tile-heading',{'height':px(heading)})
        rule('.tile-reading',{'font-size':px(38 if big else 32 if middle else 30),'line-height':px(44 if big else 36 if middle else 32)})
        rule('.tile-unit',{'font-size':px(16 if big else 15 if middle else 14),'line-height':px(20 if big else 18 if middle else 16)})
        rule('.tile-status',{'font-size':'18px','line-height':'22px'})
        rule('.tile-control .tile-status',{'height':'32px'})
        rule('.tile-control .segment button',{'height':px(button),'font-size':'18px','padding':'6px 0'})
    rules.append('#dashboard-root.layout-u80.layout-wide .climate-panel .target{font-size:60px}')
    return '<style>'+''.join(rules)+'</style>'

def render_grid(config,block,states,device,page_index):
    body='<div class="four-grid grid-h-'+str(block['rows'])+'">'
    for p in block['placements']:
        body+='<div class="grid-card grid-y-'+str(p['row'])+' grid-n-'+str(p['units'])+'" style="left:'+str(p['column']*25)+'%;right:'+str((4-p['column']-p['span'])*25)+'%">'+tile(config,p['card'],states,device,page_index,cell=True)+'</div>'
    return body+'</div>'

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
    custom_icon=config.get('icons',{}).get(entity) or item.get('attributes',{}).get('icon')
    custom_icon=custom_icon.replace('hass:','mdi:',1) if isinstance(custom_icon,str) and custom_icon.startswith('hass:') else custom_icon
    path=ICONS.get(custom_icon) or (ICONS['mdi:fan'] if entity.startswith('fan.') else ICONS['mdi:lightbulb'])
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

def entity_caption(config,entity,item):
    text='<span id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</span>'
    href=action_href(config,entity)
    return '<a class="entity-link" href="'+esc(href)+'">'+text+'</a>' if href else text

def cover_status(item):
    status=display_state('cover',item['state'],item.get('attributes',{}))
    position=item.get('attributes',{}).get('current_position')
    if item['state'] not in {'unknown','unavailable'} and isinstance(position,(int,float)) and not isinstance(position,bool) and math.isfinite(position) and 0<=position<=100:
        status+=' · '+number(position)+' %'
    return status

def cover_tile(entity,item,device,page_index,config):
    body='<div class="cover-inner"><span class="cover-label">'+entity_caption(config,entity,item)+'</span><span class="cover-state" id="'+bid(entity,'cover-status')+'">'+cover_status(item)+'</span><table class="cover-arrows"><tr>'
    for action,disabled in cover_actions(item):
        body+='<td><form method="post" action="action">'+hidden(device,entity,action)+'<input type="hidden" name="seite" value="'+str(page_index)+'"><button id="'+bid(entity,action)+'" aria-label="'+('Öffnen' if action=='open_cover' else 'Schließen')+'"'+(' disabled' if disabled or item['state'] in {'unknown','unavailable'} else '')+'>'+('↑' if action=='open_cover' else '↓')+'</button></form></td>'
    return body+'</tr></table></div>'

def script_tile(config,entity,item,device,page_index):
    return ('<form class="light-form" method="post" action="action">'+hidden(device,entity,'activate')+
        '<input type="hidden" name="seite" value="'+str(page_index)+'"><button class="light-button" id="'+bid(entity,'run')+'"'+(' disabled' if item['state'] in {'on','unknown','unavailable'} else '')+'>'+
        '<span class="light-button-icon">'+entity_icon(config,entity,item)+'</span><span class="light-button-label" id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</span></button></form>')

def action_href(config,entity):
    action=config.get('actions',{}).get(entity,{}).get('tap',{})
    if not action.get('explicit') or action.get('confirmation') or config.get('blocked_actions',{}).get(entity):return None
    if action.get('kind')=='more-info':
        target=action.get('entity') or entity
        if target not in config.get('action_entities',config['entities']):return None
        return ('/?'+urlencode({'klima':target})) if target.startswith('climate.') else '/entity?'+urlencode({'entity':target})
    if action.get('kind')=='navigate':
        path=urlsplit(action.get('navigation_path','')).path
        base='/'+config.get('dashboard_path','kindle-panel')
        if path.rstrip('/')==base:return '/'
        if path.startswith(base+'/'):
            view=unquote(path[len(base)+1:])
            if view in {v['path'] for v in config.get('dashboard_views',[])}:return '/?'+urlencode({'view':view})
    return None


def entity_detail(config,entity,item,device):
    device=dict(device,view=config.get('dashboard_view',{}).get('path'))
    config=dict(config,entities=[entity],actions={})
    card={'type':'entity','entity':entity,'columns':12,'read_only':entity not in config.get('control_entities',[])}
    body='<div class="panel">'+masthead(label(config,entity,item),device=device)+'<div class="climate-main"><a class="back" href="/">‹ Übersicht</a>'
    body+=tile(config,card,{entity:item},device,0,cell=True)
    return body+'<p>'+live_footer()+'</p></div></div><script src="/panel.js"></script>'

def tile(config,card,states,device,page_index,cell=False):
    columns=card_columns(card);width=columns*100/12
    start=('<div class="tile badge-slot" style="width:auto">' if card['type']=='badge' else '<div class="tile" style="width:'+format(width,'.5f')+'%">')
    if cell:start='<div class="tile tile-cell" style="width:100%">'
    if card['type']=='heading':return start+'<div class="tile-heading-card">'+esc(card.get('name',''))+'</div></div>'
    if card['type']=='unsupported':return start+'<div class="tile-inner"><h2 class="tile-label">'+esc(card['name'])+'</h2><p>Diese Karte wird noch nicht unterstützt.</p></div></div>'
    if card.get('template_id'):
        values=config.get('template_values',{}).get(card['template_id'],{})
        content=values.get('content','—');caption=values.get('label','')
        body='<div class="badge-pill">'
        if card.get('icon'):body+='<span class="badge-icon">'+entity_icon({'icons':{'sensor.badge':card['icon']}},'sensor.badge',{'attributes':{}})+'</span>'
        body+='<span class="badge-value" id="t-'+card['template_id']+'-content">'+esc(content)+'</span>'
        body+='<span class="badge-caption" id="t-'+card['template_id']+'-label">'+esc(caption)+'</span>'
        return start+body+'</div></div>'
    entity=card['entity'];item=states.get(entity,{'state':'unavailable','attributes':{}});attrs=item.get('attributes',{});state=item['state'];domain=entity.split('.')[0]
    if card['type']=='badge':return start+badge_tile(config,card,entity,item)+'</div>'
    href=action_href(config,entity)
    source_action=config.get('actions',{}).get(entity,{}).get('tap',{})
    if source_action.get('explicit') and source_action.get('kind') in {'more-info','navigate','url'} and domain not in {'cover','climate'}:
        tag='a' if href else 'div'
        return start+'<'+tag+' class="light-button action-link"'+(' href="'+esc(href)+'"' if href else ' aria-disabled="true"')+'><span class="light-button-icon">'+entity_icon(config,entity,item)+'</span><span class="light-button-label" id="'+bid(entity,'label')+'">'+esc(label(config,entity,item))+'</span></'+tag+'></div>'

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
    device=dict(device,view=config.get('dashboard_view',{}).get('path'))
    groups=dashboard_layout_pages(dashboard_cards(config));pages=len(groups);page_index=max(0,min(pages-1,page_index))
    view=config.get('dashboard_view',{});view_path=view.get('path');title=view.get('title','Zuhause')
    query=lambda index:'?'+urlencode(dict({'seite':index},**({'view':view_path} if view_path else {})))
    rows=sum(block.get('rows',0) for block in groups[page_index])
    fit_rows=max(sum(block.get('rows',0) if block['kind']=='grid' else math.ceil(block['height']/GRID_UNIT) for block in group) for group in groups)
    display_class='panel dashboard layout-u52'
    body='<div class="'+display_class+'" id="dashboard-root" data-grid-rows="'+str(rows)+'" data-fit-rows="'+str(fit_rows)+'" data-layout-preferred="'+str(config.get('preferred_layout_unit',0))+'" data-revision="'+esc(config.get('dashboard_revision',''))+'">'+masthead(title,query(page_index),device=device)
    views=config.get('dashboard_views',[])
    if len(views)>1:
        body+='<nav class="view-tabs">'
        for item in views:body+='<a class="view-tab'+(' active' if item['path']==view_path else '')+'" href="?'+urlencode({'view':item['path']})+'">'+esc(item['title'])+'</a>'
        body+='</nav>'
    if not any(groups):
        body+='<div class="empty-state">Dieses Dashboard ist noch leer.</div>'
    body+=layout_css(groups[page_index])+'<div class="dashboard-grid">'
    for block in groups[page_index]:
        if block['kind']=='badges':
            body+='<div class="dashboard-badges">'+''.join(tile(config,c,states,device,page_index) for c in block['cards'])+'</div>'
        elif block['kind']=='heading':
            body+='<div class="tile-heading-card">'+esc(block['cards'][0]['name'])+'</div>'
        else:body+=render_grid(config,block,states,device,page_index)
    body+='</div>'
    body+='<footer class="bottom"><div class="live-line">'+live_footer()+'</div>'
    if pages>1:
        body+='<nav class="pagination" aria-label="Dashboard-Seiten">'
        body+='<a class="pager"'+(' href="'+query(page_index-1)+'"' if page_index else ' aria-disabled="true"')+'>Zurück</a>'
        body+='<span class="page-count">'+str(page_index+1)+' / '+str(pages)+'</span>'
        body+='<a class="pager"'+(' href="'+query(page_index+1)+'"' if page_index+1<pages else ' aria-disabled="true"')+'>Weiter</a></nav>'
    return body+'</footer></div><script src="/layout.js"></script><script src="/panel.js"></script>'

def climate_panel(config,entity,item,device,more=False):
    attrs=item.get('attributes',{});unit=attrs.get('temperature_unit','');state=item['state'];available=state not in {'unknown','unavailable'} and not config.get('read_only',{}).get(entity,False)
    body='<div class="climate-panel"><div class="climate-heading">'
    if more:body+='<a class="climate-info" href="?'+esc(urlencode(dict({'klima':entity},**({'view':config['dashboard_view']['path']} if config.get('dashboard_view',{}).get('path') else {}))))+'" aria-label="Weitere Klimaeinstellungen" title="Weitere Klimaeinstellungen">ⓘ</a>'
    body+='<h2>'+entity_caption(config,entity,item)+'</h2></div>'
    if not more:body+='<div class="mode-status" id="'+bid(entity,'state')+'">'+display_state('climate',state,attrs)+'</div>'
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
    modes=climate_modes(config,entity,attrs)
    if modes:
        body+='<table class="mode-buttons"><tr>'
        for mode in modes:
            body+='<td><form method="post" action="action">'+hidden(device,entity,'climate_hvac')+'<button id="'+bid(entity,'mode-'+mode)+'" class="mode-button'+(' active' if state==mode else '')+'" name="value" value="'+mode+'" title="'+esc(MODES[mode])+'" aria-label="'+esc(MODES[mode])+'"'+(' disabled' if not available else '')+'>'+MODE_ICONS[mode]+'</button></form></td>'
        body+='</tr></table>'
    return body+'</div>'

def climate(config,entity,item,device):
    device=dict(device,view=config.get('dashboard_view',{}).get('path'))
    attrs=item.get('attributes',{});available=item['state'] not in {'unknown','unavailable'} and not config.get('read_only',{}).get(entity,False)
    body='<div class="panel"><div class="climate-main climate-detail"><div style="float:right">'+exit_form(device)+'</div><a class="back" href="./">‹ Übersicht</a><div style="clear:both"></div>'+climate_panel(config,entity,item,device)
    for title,action,values,current,names in settings(item):
        if action=='climate_hvac' or not values:continue
        body+='<section class="setting-row"><h2>'+title+'</h2><form method="post" action="action">'+hidden(device,entity,action)+'<table class="apply-table"><tr><td><select id="'+bid(entity,action)+'" name="value"'+(' disabled' if not available else '')+'>'
        for value in values:
            body+='<option value="'+esc(value)+'"'+(' selected' if value==current else '')+'>'+esc(setting_name(value,names))+'</option>'
        body+='</select></td><td class="apply"><button id="'+bid(entity,action+'-apply')+'"'+(' disabled' if not available else '')+'>Setzen</button></td></tr></table></form></section>'
    return body+'<p class="climate-foot">−/+ ändert nur die Solltemperatur. Die Symbole darunter setzen direkt die Betriebsart.</p><p class="climate-foot">'+live_footer()+'</p></div></div><script src="/panel.js"></script>'
