import unittest
from ha_dashboard import translate,view_config,seed,ensure_dashboard,PATH,Source
import ui

class DashboardTests(unittest.TestCase):
    def test_sections_names_widths_and_room_views(self):
        raw={'views':[{'title':'Büro','path':'office','type':'sections','sections':[{'type':'grid','cards':[
            {'type':'tile','entity':'sensor.temperature','name':'Temperatur','grid_options':{'columns':3}},
            {'type':'thermostat','entity':'climate.office','grid_options':{'columns':12}}]}]},
            {'title':'Kind','path':'child','cards':[{'type':'tile','entity':'sensor.temperature','name':'Andere Beschriftung'}]}]}
        model=translate(raw);office=view_config({},model,'office');child=view_config({},model,'child')
        self.assertEqual(office['columns']['sensor.temperature'],3)
        self.assertEqual(office['labels']['sensor.temperature'],'Temperatur')
        self.assertEqual(child['labels']['sensor.temperature'],'Andere Beschriftung')
        self.assertEqual(office['entities'],['sensor.temperature','climate.office'])
        self.assertEqual(model['control_entities'],['climate.office'])

    def test_unsupported_and_conditional_cards_never_grant_controls(self):
        model=translate({'views':[{'cards':[{'type':'custom:anything','entity':'light.private'},
            {'type':'tile','entity':'switch.conditional','visibility':[{'condition':'state'}]},
            {'type':'tile','entity':'light.readonly','tap_action':{'action':'none'}},
            {'type':'tile','entity':'light.script','tap_action':{'action':'perform-action','perform_action':'script.private'}}]}]})
        self.assertNotIn('light.private',model['entities'])
        self.assertNotIn('switch.conditional',model['entities'])
        self.assertEqual(model['control_entities'],[])
        self.assertTrue(model['warnings'])

    def test_stacks_and_entities_are_translated_without_html(self):
        model=translate({'views':[{'cards':[{'type':'horizontal-stack','cards':[
            {'type':'tile','entity':'sensor.a','name':'<script>bad</script>'},
            {'type':'tile','entity':'binary_sensor.door'}]},
            {'type':'entities','entities':['sensor.b',{'entity':'switch.c'}]}]}]})
        config=view_config({},model)
        self.assertEqual(config['entities'],['sensor.a','binary_sensor.door','sensor.b','switch.c'])
        self.assertEqual(config['columns']['sensor.a'],6)
        self.assertEqual(config['labels']['sensor.a'],'<script>bad</script>')

    def test_view_badges_precede_sections_and_are_live_read_only_entities(self):
        model=translate({'views':[{'path':'child','type':'sections','badges':[
            {'type':'entity','entity':'sensor.temperature','name':'Temperatur','icon':'mdi:thermometer'},
            'sensor.humidity',{'type':'entity','entity':'binary_sensor.motion'}],
            'sections':[{'type':'grid','cards':[{'type':'thermostat','entity':'climate.child'}]}]},
            {'path':'office','cards':[],'badges':['sensor.office']}]})
        child=view_config({},model,'child');office=view_config({},model,'office')
        self.assertEqual(child['entities'],['sensor.temperature','sensor.humidity','binary_sensor.motion','climate.child'])
        self.assertEqual(child['columns']['sensor.temperature'],3)
        self.assertEqual(child['labels']['sensor.temperature'],'Temperatur')
        self.assertEqual(child['icons']['sensor.temperature'],'mdi:thermometer')
        self.assertTrue(child['read_only']['sensor.humidity'])
        self.assertEqual(model['control_entities'],['climate.child'])
        self.assertEqual(office['entities'],['sensor.office'])

    def test_badges_skip_conditions_custom_types_and_duplicate_cards(self):
        model=translate({'views':[{'cards':[{'type':'tile','entity':'light.room'}], 'badges':[
            {'type':'entity','entity':'light.room'},
            {'type':'entity','entity':'sensor.hidden','visibility':[{'condition':'state'}]},
            {'type':'entity-filter','entities':['sensor.filtered'],'conditions':[{'condition':'state'}]},
            {'type':'custom:test','entity':'sensor.private'},
            {'type':'entity','entity':'sensor.attribute','state_content':['temperature']},
            'sensor.visible','sensor.visible']}]})
        config=view_config({},model)
        self.assertEqual(config['entities'],['sensor.visible','light.room'])
        self.assertEqual(model['control_entities'],['light.room'])
        self.assertEqual(len(config['entities']),len(set(config['entities'])))
        self.assertTrue(model['warnings'])

    def test_display_precision_and_registry_icon_are_used_in_badges_and_live_patches(self):
        raw={'views':[{'badges':[{'type':'entity','entity':'sensor.temp'},'sensor.humidity'],'cards':[]}]}
        model=translate(raw,{'sensor.temp':{'precision':1,'icon':'mdi:thermometer-lines'},'sensor.humidity':{'precision':0}})
        config=view_config({},model)
        states={'sensor.temp':{'state':'21','attributes':{'unit_of_measurement':'°C'}},
            'sensor.humidity':{'state':'48.5','attributes':{'unit_of_measurement':'%'}}}
        markup=ui.dashboard(config,states,{'csrf':'test'},0,30)
        self.assertIn('id="e-sensor-temp-value">21,0</span>',markup)
        self.assertIn('id="e-sensor-humidity-value">49</span>',markup)
        self.assertIn('badge-pill',markup)
        self.assertNotIn('tile-label',markup)
        self.assertIn(ui.ICONS['mdi:thermometer-lines'],markup)
        patches=ui.updates(config,states)['patches']
        self.assertEqual(next(p['text'] for p in patches if p['id']=='e-sensor-temp-value'),'21,0')
        self.assertEqual(ui.sensor_number(config,'sensor.humidity','-1.5'),'-2')
        self.assertEqual(ui.sensor_number(config,'sensor.temp','0'),'0,0')
        self.assertEqual(ui.sensor_number(config,'sensor.temp','unavailable'),'unavailable')
        self.assertNotEqual(model['revision'],translate(raw,{'sensor.temp':{'precision':2}})['revision'])

    def test_source_reads_home_assistant_display_metadata(self):
        def call(requests):
            kind=requests[0]['type']
            if kind=='lovelace/dashboards/list':return [[{'url_path':PATH}]]
            if kind=='config/entity_registry/list_for_display':return [{'entities':[
                {'ei':'sensor.temp','dp':1,'ic':'mdi:thermometer'},
                {'ei':'sensor.private','dp':2,'ic':'mdi:home'}]}]
            if kind=='lovelace/config':return [{'views':[{'badges':['sensor.temp'],'cards':[]}]}]
            raise AssertionError(kind)
        source=Source(call);source.refresh({},[PATH])
        model=source.model(PATH)
        self.assertEqual(model['display'],{'sensor.temp':{'precision':1,'icon':'mdi:thermometer'}})
        self.assertEqual(source.status()['errors'],{})

    def test_existing_dashboard_is_never_overwritten(self):
        calls=[]
        def call(requests):
            calls.extend(requests)
            return [[{'url_path':PATH}]] if requests[0]['type']=='lovelace/dashboards/list' else [{'views':[]}]
        ensure_dashboard({'entities':['sensor.a']},call)
        self.assertEqual([c['type'] for c in calls],['lovelace/dashboards/list','lovelace/config'])

    def test_new_dashboard_created_from_current_selection_once(self):
        calls=[]
        def call(requests):
            calls.extend(requests)
            if requests[0]['type']=='lovelace/dashboards/list':return [[]]
            return [{'views':[]} for request in requests]
        ensure_dashboard({'entities':['sensor.a','climate.b'],'labels':{'sensor.a':'Temperatur'}},call)
        save=next(c for c in calls if c['type']=='lovelace/config/save')
        cards=save['config']['views'][0]['sections'][0]['cards']
        self.assertEqual(cards[0]['name'],'Temperatur')
        self.assertEqual(cards[0]['grid_options']['columns'],3)
        self.assertEqual(cards[1]['type'],'thermostat')
        self.assertEqual([c['url_path'] for c in calls if 'url_path' in c],[PATH,PATH,PATH])

if __name__=='__main__':unittest.main()
