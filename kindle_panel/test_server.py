import http.client
import json
import ha_dashboard
import tempfile
import threading
import unittest
from urllib.parse import urlencode
from server import App, COOKIE, digest, make_server

class PanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.calls = []
        self.states = {
            'light.test': {'entity_id':'light.test','state':'off','attributes':{'friendly_name':'<script>unsafe</script>'}},
            'light.other': {'entity_id':'light.other','state':'on','attributes':{}},
            'scene.test': {'entity_id':'scene.test','state':'unknown','attributes':{}},
            'sensor.test': {'entity_id':'sensor.test','state':'21','attributes':{'unit_of_measurement':'°C'}}}
        def api(path, payload):
            if path == 'states': return list(self.states.values())
            if path.startswith('states/'): return self.states[path[7:]]
            if path == 'config': return {'unit_system': {'temperature': '°C'}}
            self.calls.append((path,payload)); return []
        self.app = App(self.temp.name,api)
        self.app.set_entities(['light.test','sensor.test','scene.test'])
        self.public = make_server(self.app,('127.0.0.1',0))
        self.admin = make_server(self.app,('127.0.0.1',0),admin=True,ingress_ip='127.0.0.1')
        for server in (self.public,self.admin):
            threading.Thread(target=server.serve_forever,daemon=True).start()

    def tearDown(self):
        for server in (self.public,self.admin): server.shutdown();server.server_close()
        self.temp.cleanup()

    def request(self, server, method='GET', path='/', data=None, headers=None):
        connection = http.client.HTTPConnection(*server.server_address)
        body = urlencode(data) if data is not None else None
        h = headers or {}
        if body is not None: h = dict(h, **{'Content-Type':'application/x-www-form-urlencoded'})
        connection.request(method,path,body,h)
        response=connection.getresponse(); result=(response.status,dict(response.getheaders()),response.read().decode())
        connection.close(); return result

    def pair(self):
        status, headers, body=self.request(self.public)
        self.assertEqual(status,200)
        self.assertIn('Kindle verbinden',body)
        token=headers['Set-Cookie'].split(';')[0].split('=',1)[1]
        state=self.app.snapshot()
        self.assertEqual(self.request(self.admin,'POST','/admin/approve',{'csrf':state['admin_csrf'],'device':digest(token)},{'X-Remote-User-Id':'test-user'})[0],303)
        return token,self.app.device(token)

    def test_pending_device_cannot_control(self):
        token,device=self.app.register('127.0.0.1')
        with self.assertRaises(PermissionError): self.app.control(token,device['csrf'],'light.test','turn_on')
        self.assertEqual(self.calls,[])

    def test_pairing_and_html_controls(self):
        token,device=self.pair()
        headers={'Cookie':COOKIE+'='+token}
        status,_,body=self.request(self.public,headers=headers)
        self.assertEqual(status,200)
        self.assertNotIn('<script>',body)
        self.assertIn('&lt;script&gt;',body)
        self.assertEqual(self.request(self.public,'POST','/action',{'csrf':device['csrf'],'entity':'light.test','action':'turn_on'},headers)[0],303)
        self.assertEqual(self.calls,[('services/light/turn_on',{'entity_id':'light.test'})])

    def test_public_cannot_configure_even_with_spoofed_headers(self):
        headers={'X-Remote-User-Id':'admin','X-Forwarded-For':'172.30.32.2'}
        self.assertEqual(self.request(self.public,path='/admin/',headers=headers)[0],404)
        self.assertEqual(self.request(self.public,'POST','/admin/save',{'csrf':self.app.snapshot()['admin_csrf']},headers)[0],403)
        self.assertEqual(self.request(self.admin,path='/admin/')[0],403)

    def test_csrf_and_unselected_entity_blocked(self):
        token,device=self.pair()
        with self.assertRaises(PermissionError): self.app.control(token,'invalid','light.test','turn_on')
        with self.assertRaises(ValueError): self.app.control(token,device['csrf'],'light.other','turn_on')
        with self.assertRaises(ValueError): self.app.control(token,device['csrf'],'sensor.test','turn_on')
        self.assertEqual(self.calls,[])

    def test_stale_selection_and_unavailable_entity_blocked(self):
        token,device=self.pair()
        self.states['light.test']['state']='unavailable'
        with self.assertRaises(ValueError): self.app.control(token,device['csrf'],'light.test','turn_on')
        self.app.set_entities(['light.other'])
        with self.assertRaises(ValueError): self.app.control(token,device['csrf'],'light.test','turn_on')
        self.assertEqual(self.calls,[])

    def test_scene_unknown_can_activate_and_revocation_works(self):
        token,device=self.pair()
        self.app.control(token,device['csrf'],'scene.test','activate')
        self.assertEqual(self.calls,[('services/scene/turn_on',{'entity_id':'scene.test'})])
        del self.app.data['devices'][digest(token)]
        with self.assertRaises(PermissionError): self.app.control(token,device['csrf'],'light.test','turn_on')

    def test_persistence_and_admin_csrf(self):
        token,_=self.pair()
        self.assertEqual(App(self.temp.name).device(token)['approved'],True)
        self.assertEqual(self.request(self.admin,'POST','/admin/save',{'csrf':'wrong','entity0':'light.other'},{'X-Remote-User-Id':'test-user'})[0],403)
        self.assertEqual(self.app.snapshot()['entities'],['light.test','sensor.test','scene.test'])

    def test_live_requires_approved_device_and_revocation(self):
        for path in ('/live', '/live.json', '/live.js'):
            self.assertEqual(self.request(self.public,path=path)[0],403)
        token,device=self.app.register('127.0.0.1')
        headers={'Cookie':COOKIE+'='+token}
        self.assertEqual(self.request(self.public,path='/live.json',headers=headers)[0],403)
        self.app.data['devices'][digest(token)]['approved']=True
        status,_,body=self.request(self.public,path='/live',headers=headers)
        self.assertEqual(status,200)
        self.assertNotIn('http-equiv="refresh"',body)
        self.assertIn('src="/live.js"',body)
        del self.app.data['devices'][digest(token)]
        self.assertEqual(self.request(self.public,path='/live.json',headers=headers)[0],403)

    def test_live_selected_sensors_only_and_updated_values(self):
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        self.states['sensor.private']={'entity_id':'sensor.private','state':'secret','attributes':{}}
        status,response_headers,body=self.request(self.public,path='/live.json',headers=headers)
        self.assertEqual(status,200)
        self.assertIn('application/json',response_headers['Content-Type'])
        readings=json.loads(body)['readings']
        self.assertEqual([i['entity'] for i in readings],['sensor.test'])
        self.assertEqual(readings[0]['value'],'21')
        self.assertNotIn('secret',body)
        self.assertNotIn('csrf',body)
        self.states['sensor.test']['state']='22.5'
        self.app.live_cache=None
        self.assertEqual(json.loads(self.request(self.public,path='/live.json',headers=headers)[2])['readings'][0]['value'],'22,5')
        self.assertEqual(self.calls,[])
        self.app.set_entities([])
        self.assertEqual(json.loads(self.request(self.public,path='/live.json',headers=headers)[2])['readings'],[])

    def test_live_failure_is_json_and_does_not_serve_stale_cache(self):
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        self.request(self.public,path='/live.json',headers=headers)
        self.app.live_cache=None
        def broken(path,payload): raise RuntimeError('secret upstream message')
        self.app.api_override=broken
        status,_,body=self.request(self.public,path='/live.json',headers=headers)
        self.assertEqual(status,503)
        self.assertEqual(json.loads(body),{'error':'upstream_unavailable'})

    def test_panel_updates_require_approval_and_only_selected_entities(self):
        self.assertEqual(self.request(self.public,path='/updates.json')[0],403)
        self.assertEqual(self.request(self.public,path='/panel.js')[0],403)
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        status,_,body=self.request(self.public,path='/updates.json',headers=headers)
        self.assertEqual(status,200)
        data=json.loads(body)
        self.assertEqual(set(data['entities']),{'light.test','sensor.test','scene.test'})
        self.assertNotIn('light.other',body);self.assertNotIn('csrf',body)
        self.assertIn({'id':'e-sensor-test-value','text':'21'},data['patches'])
        del self.app.data['devices'][digest(token)]
        self.assertEqual(self.request(self.public,path='/updates.json',headers=headers)[0],403)

    def test_async_action_checks_csrf_and_invalidates_cache(self):
        token,device=self.pair();headers={'Cookie':COOKIE+'='+token}
        self.app.panel_snapshot()
        self.assertIsNotNone(self.app.panel_cache)
        status,_,body=self.request(self.public,'POST','/action.json',{'csrf':device['csrf'],'entity':'light.test','action':'turn_on'},headers)
        self.assertEqual(status,202);self.assertEqual(json.loads(body),{'accepted':True})
        self.assertIsNone(self.app.panel_cache)
        self.assertEqual(self.request(self.public,'POST','/action.json',{'csrf':'bad','entity':'light.test','action':'turn_on'},headers)[0],403)
        self.assertEqual(self.request(self.public,'POST','/action.json',{'csrf':device['csrf'],'entity':'light.other','action':'turn_on'},headers)[0],400)
        self.assertEqual(self.calls,[('services/light/turn_on',{'entity_id':'light.test'})])

    def test_climate_live_patches_update_steps_and_availability(self):
        self.add_climate(); token,_=self.pair(); headers={'Cookie':COOKIE+'='+token}
        def patches():
            self.app.panel_cache=None
            data=json.loads(self.request(self.public,path='/updates.json',headers=headers)[2])
            return {item['id']:item for item in data['patches']}
        data=patches()
        self.assertEqual(data['e-climate-test-plus']['value'],'25.0')
        self.assertEqual(data['e-climate-test-target']['text'],'24,5')
        self.states['climate.test']['attributes']['temperature']=30
        data=patches();self.assertTrue(data['e-climate-test-plus']['disabled'])
        self.states['climate.test']['state']='unavailable'
        data=patches();self.assertTrue(data['e-climate-test-minus']['disabled'])
        self.assertTrue(data['e-climate-test-climate_hvac-apply']['disabled'])
        self.assertEqual(self.calls,[])

    def test_visible_exit_authentication_and_counter_persistence(self):
        status,headers,body=self.request(self.public,path='/kiosk-status')
        self.assertEqual(status,200);self.assertEqual(body,'0')
        self.assertIn('text/plain',headers['Content-Type'])
        self.assertEqual(self.request(self.public,'POST','/kiosk-exit',{'csrf':'bad'})[0],403)
        token,device=self.pair();headers={'Cookie':COOKIE+'='+token}
        self.assertEqual(self.request(self.public,'POST','/kiosk-exit',{'csrf':'bad'},headers)[0],403)
        self.assertEqual(self.request(self.public,path='/kiosk-exit',headers=headers)[0],404)
        self.assertEqual(self.request(self.public,'POST','/kiosk-exit',{'csrf':device['csrf']},headers)[0],200)
        self.assertEqual(self.request(self.public,path='/kiosk-status')[2],'1')
        self.assertEqual(App(self.temp.name).snapshot()['exit_generation'],1)
        self.assertEqual(self.calls,[])
        del self.app.data['devices'][digest(token)]
        self.assertEqual(self.request(self.public,'POST','/kiosk-exit',{'csrf':device['csrf']},headers)[0],403)
        self.assertEqual(self.request(self.public,path='/kiosk-status')[2],'1')

    def test_visible_exit_present_on_dashboard_and_climate(self):
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        self.assertIn('action="/kiosk-exit"',self.request(self.public,headers=headers)[2])
        self.add_climate()
        body=self.request(self.public,path='/?klima=climate.test',headers=headers)[2]
        self.assertIn('Home Assistant verlassen',body);self.assertIn('action="/kiosk-exit"',body)

    def test_direct_climate_modes_wait_for_confirmed_state(self):
        self.add_climate();token,device=self.pair();headers={'Cookie':COOKIE+'='+token}
        body=self.request(self.public,path='/?klima=climate.test',headers=headers)[2]
        for mode in ['off','fan_only','heat','cool','heat_cool','dry']:
            self.assertIn('id="e-climate-test-mode-'+mode+'"',body)
        self.assertNotIn('id="e-climate-test-mode-auto"',body)
        self.assertNotIn('<select id="e-climate-test-climate_hvac"',body)
        def active(mode):
            self.app.panel_cache=None
            data=self.app.panel_snapshot()
            return next(p for p in data['patches'] if p['id']=='e-climate-test-mode-'+mode)
        self.assertEqual(active('off')['className'],'mode-button active')
        status,_,_=self.request(self.public,'POST','/action.json',{'csrf':device['csrf'],'entity':'climate.test','action':'climate_hvac','value':'cool'},headers)
        self.assertEqual(status,202)
        self.assertEqual(active('cool')['className'],'mode-button')
        self.states['climate.test']['state']='cool'
        self.assertEqual(active('cool')['className'],'mode-button active')
        self.assertEqual(active('off')['className'],'mode-button')
        self.assertEqual(self.calls,[('services/climate/set_hvac_mode',{'entity_id':'climate.test','hvac_mode':'cool'})])
        self.states['climate.test']['attributes']['hvac_modes'].remove('cool')
        self.assertTrue(active('cool')['disabled'])

    def test_overview_compact_statuses_and_full_climate_fit(self):
        self.add_climate()
        for name in ['second','third','fourth']:
            self.states['sensor.'+name]={'entity_id':'sensor.'+name,'state':'20','attributes':{}}
        self.app.set_entities(['sensor.test','sensor.second','sensor.third','sensor.fourth','climate.test','light.test'])
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        body=self.request(self.public,headers=headers)[2]
        self.assertIn('id="e-climate-test-plus"',body)
        self.assertIn('id="e-light-test-on"',body)
        self.assertEqual(body.count('style="width:25.00000%"'),4)
        self.assertIn('style="width:100.00000%"',body)
        self.assertNotIn('colspan=',body)

    def install_room_source(self):
        models={path:ha_dashboard.translate({'views':[{'title':path,'path':'home','cards':[{'type':'tile','entity':entity}]}]})
            for path,entity in [('office-panel','light.test'),('child-panel','light.other')]}
        class Source:
            def model(self,path):return models[path]
            def refresh(self,*args,**kwargs):pass
            def status(self):return {'dashboards':[{'url_path':p,'title':p} for p in models],'errors':{},'warnings':{}}
        self.app.dashboard_source=Source()

    def test_kindles_are_scoped_to_their_assigned_dashboards(self):
        a,da=self.pair();b,db=self.pair();self.install_room_source()
        self.app.data['devices'][digest(a)]['dashboard_path']='office-panel'
        self.app.data['devices'][digest(b)]['dashboard_path']='child-panel'
        first=json.loads(self.request(self.public,path='/updates.json',headers={'Cookie':COOKIE+'='+a})[2])
        second=json.loads(self.request(self.public,path='/updates.json',headers={'Cookie':COOKIE+'='+b})[2])
        self.assertEqual(set(first['entities']),{'light.test'})
        self.assertEqual(set(second['entities']),{'light.other'})
        with self.assertRaises(ValueError):self.app.control(a,da['csrf'],'light.other','turn_on')
        with self.assertRaises(ValueError):self.app.control(b,db['csrf'],'light.test','turn_on')
        self.assertEqual(self.calls,[])

    def test_dashboard_assignment_persists_and_device_name_is_escaped(self):
        a,_=self.pair();b,_=self.pair();self.install_room_source()
        self.app.data['devices'][digest(b)]['dashboard_path']='child-panel'
        status,_,_=self.request(self.admin,'POST','/admin/assign',{
            'csrf':self.app.snapshot()['admin_csrf'],'device':digest(a),
            'dashboard':'office-panel','name':'<Büro>','view':'home'},
            {'X-Remote-User-Id':'admin'})
        self.assertEqual(status,303)
        stored=json.loads(self.app.path.read_text())['devices']
        self.assertEqual(stored[digest(a)]['dashboard_path'],'office-panel')
        self.assertEqual(stored[digest(a)]['view_path'],'home')
        self.assertEqual(stored[digest(b)]['dashboard_path'],'child-panel')
        body=self.request(self.admin,path='/admin/',headers={'X-Remote-User-Id':'admin'})[2]
        self.assertIn('&lt;Büro&gt;',body)
        self.assertNotIn('<Büro>',body)
        with self.assertRaises(ValueError):self.app.assign_dashboard(digest(a),'missing','Büro')

    def test_unavailable_room_does_not_fall_back_to_another_dashboard(self):
        a,_=self.pair();self.install_room_source()
        self.app.data['devices'][digest(a)]['dashboard_path']='missing'
        status,_,body=self.request(self.public,path='/updates.json',headers={'Cookie':COOKIE+'='+a})
        self.assertEqual(status,503)
        self.assertNotIn('light.test',body)
        self.assertNotIn('light.other',body)

    def test_badge_only_view_renders_and_updates_temperature_and_humidity(self):
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        self.states['sensor.humidity']={'entity_id':'sensor.humidity','state':'48','attributes':{'unit_of_measurement':'%'}}
        model=ha_dashboard.translate({'views':[{'badges':['sensor.test','sensor.humidity'],'cards':[]}]})
        class Source:
            def model(self,path):return model
        self.app.dashboard_source=Source()
        status,_,body=self.request(self.public,headers=headers)
        self.assertEqual(status,200)
        self.assertIn('id="e-sensor-test-value">21</div>',body)
        self.assertIn('id="e-sensor-humidity-value">48</div>',body)
        self.assertIn('id="e-sensor-humidity-unit">%</span>',body)
        self.states['sensor.humidity']['state']='51'
        self.states['sensor.test']['state']='22.5'
        data=json.loads(self.request(self.public,path='/updates.json',headers=headers)[2])
        self.assertEqual(data['entities']['sensor.humidity']['state'],'51')
        self.assertEqual(data['entities']['sensor.test']['state'],'22.5')
        self.assertNotIn('light.test',data['entities'])
        self.assertEqual(self.calls,[])

    def test_each_kindles_exit_signal_is_separate(self):
        a,da=self.pair();b,db=self.pair();ca='a'*32;cb='b'*32
        self.app.bind_controller(a,ca);self.app.bind_controller(b,cb)
        status=self.request(self.public,'POST','/kiosk-exit',{'csrf':da['csrf'],'controller':ca},{'Cookie':COOKIE+'='+a})[0]
        self.assertEqual(status,200)
        self.assertEqual(self.request(self.public,path='/kiosk-status?controller='+ca)[2],'1')
        self.assertEqual(self.request(self.public,path='/kiosk-status?controller='+cb)[2],'0')
        self.assertEqual(self.request(self.public,path='/kiosk-status')[2],'0')
        self.assertEqual(self.request(self.public,'POST','/kiosk-exit',{'csrf':da['csrf'],'controller':cb},{'Cookie':COOKIE+'='+a})[0],403)

    def test_admin_preview_has_no_forms_or_control_scripts(self):
        token,_=self.pair();self.install_room_source()
        self.app.data['devices'][digest(token)]['dashboard_path']='office-panel'
        status,_,body=self.request(self.admin,path='/admin/preview?device='+digest(token),headers={'X-Remote-User-Id':'admin'})
        self.assertEqual(status,200)
        self.assertNotIn('<form',body);self.assertNotIn('panel.js',body)
        self.assertIn('e-light-test-on',body)
        self.assertEqual(self.calls,[])
        self.assertEqual(self.request(self.public,path='/admin/preview')[0],404)

    def add_climate(self):
        self.states['climate.test']={'entity_id':'climate.test','state':'off','attributes':{
            'friendly_name':'Kinderzimmer','supported_features':953,'min_temp':10,'max_temp':30,
            'target_temp_step':0.5,'current_temperature':20,'temperature':24.5,
            'hvac_modes':['off','fan_only','heat','cool','heat_cool','dry'],
            'fan_modes':['auto','quiet','1','2','3','4','5'],'fan_mode':'auto'}}
        self.app.set_entities(['climate.test'])

    def test_climate_temperature_does_not_change_mode(self):
        self.add_climate();token,device=self.pair()
        status,headers,_=self.request(self.public,'POST','/action',{
            'csrf':device['csrf'],'entity':'climate.test','action':'climate_temperature','value':'24,0'},
            {'Cookie':COOKIE+'='+token})
        self.assertEqual(status,303)
        self.assertEqual(headers['Location'],'./?klima=climate.test')
        self.assertEqual(self.calls,[('services/climate/set_temperature',{'entity_id':'climate.test','temperature':24.0})])
        self.assertEqual(self.states['climate.test']['state'],'off')

    def test_climate_limits_steps_modes_and_features(self):
        self.add_climate();token,device=self.pair()
        for value in ('9.5','30.5','22.1','NaN','Infinity','not-a-number'):
            with self.assertRaises(ValueError):self.app.control(token,device['csrf'],'climate.test','climate_temperature',value)
        with self.assertRaises(ValueError):self.app.control(token,device['csrf'],'climate.test','climate_hvac','auto')
        with self.assertRaises(ValueError):self.app.control(token,device['csrf'],'climate.test','climate_fan','turbo')
        self.assertEqual(self.calls,[])
        self.states['climate.test']['attributes']['supported_features']=0
        with self.assertRaises(ValueError):self.app.control(token,device['csrf'],'climate.test','climate_temperature','24')
        with self.assertRaises(ValueError):self.app.control(token,device['csrf'],'climate.test','climate_fan','auto')

    def test_climate_supported_mode_and_fan(self):
        self.add_climate();token,device=self.pair()
        self.app.control(token,device['csrf'],'climate.test','climate_hvac','cool')
        self.app.control(token,device['csrf'],'climate.test','climate_fan','quiet')
        self.assertEqual(self.calls,[('services/climate/set_hvac_mode',{'entity_id':'climate.test','hvac_mode':'cool'}),('services/climate/set_fan_mode',{'entity_id':'climate.test','fan_mode':'quiet'})])

    def test_climate_page_and_selection_gate(self):
        self.add_climate();token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        status,_,body=self.request(self.public,path='/?klima=climate.test',headers=headers)
        self.assertEqual(status,200)
        self.assertIn('24,5',body);self.assertIn('Aktuell 20 °C',body)
        self.assertIn('climate_temperature',body);self.assertIn('src="/panel.js"',body);self.assertNotIn('http-equiv="refresh"',body)
        self.app.set_entities([])
        self.assertEqual(self.request(self.public,path='/?klima=climate.test',headers=headers)[0],404)

    def test_pagination_and_custom_labels(self):
        for i in range(8):self.states['sensor.n'+str(i)]={'entity_id':'sensor.n'+str(i),'state':str(i),'attributes':{'friendly_name':'Measurement '+str(i)}}
        entities=['sensor.n'+str(i) for i in range(8)]
        self.app.set_entities(entities,{'sensor.n7':'<short name>'})
        token,_=self.pair();headers={'Cookie':COOKIE+'='+token}
        body=self.request(self.public,path='/?seite=1',headers=headers)[2]
        self.assertIn('&lt;short name&gt;',body)
        self.assertIn('Measurement 0',body)

    def test_invalid_label_does_not_change_selection(self):
        previous=self.app.snapshot()['entities']
        with self.assertRaises(ValueError):self.app.set_entities(['light.other'],{'light.other':'x'*61})
        self.assertEqual(self.app.snapshot()['entities'],previous)

if __name__=='__main__': unittest.main()
