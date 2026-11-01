import unittest
from ha_dashboard import translate,view_config,seed,ensure_dashboard,PATH

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
