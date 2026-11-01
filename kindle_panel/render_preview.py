from pathlib import Path
import subprocess,tempfile
import ui
from server import page
base=Path(__file__).resolve().parents[1]/'outputs'
base.mkdir(exist_ok=True)
climate={'state':'off','attributes':{'friendly_name':'Kinderzimmer Klimaanlage','supported_features':953,'min_temp':10,'max_temp':30,'target_temp_step':0.5,'temperature':24.5,'current_temperature':20,'temperature_unit':'°C','hvac_modes':['off','fan_only','heat','cool','heat_cool','dry'],'fan_modes':['auto','quiet','1','2','3','4','5'],'fan_mode':'auto'}}
states={'light.wohnen':{'state':'on','attributes':{'friendly_name':'Wohnzimmer'}},'light.essen':{'state':'off','attributes':{'friendly_name':'Esstisch'}},'sensor.temperatur':{'state':'21.6','attributes':{'friendly_name':'Raumtemperatur','unit_of_measurement':'°C'}},'climate.kinderzimmer':climate,'scene.abend':{'state':'unknown','attributes':{'friendly_name':'Guten Abend'}},'binary_sensor.fenster':{'state':'off','attributes':{'friendly_name':'Terrassenfenster','device_class':'window'}}}
config={'entities':list(states),'labels':{'climate.kinderzimmer':'Kinderzimmer'}}
device={'csrf':'preview-not-a-real-session'}
for name,width,height,body in [('dashboard-758',758,1024,ui.dashboard(config,states,device,0,30)),('dashboard-600',600,800,ui.dashboard(config,states,device,0,30)),('climate-600',600,800,ui.climate(config,'climate.kinderzimmer',climate,device))]:
    html=base/(name+'.html');html.write_text(page('Layoutvorschau',body,kindle=True))
    image=base/(name+'.png')
    with tempfile.TemporaryDirectory(prefix='kindle-preview-chrome-') as profile:
        result=subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+profile,'--window-size='+str(width)+','+str(height),'--screenshot='+str(image),html.as_uri()],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
        if result.returncode:raise RuntimeError(result.stderr.decode()[-1000:])
    assert image.stat().st_size>1000
    print(image)
