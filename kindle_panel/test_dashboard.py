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
        self.assertNotIn('id="e-sensor-temp-label"',markup)
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

    def test_heading_and_unsupported_cards_do_not_become_entity_labels(self):
        model=translate({'views':[{'cards':[{'type':'heading','heading':'Beleuchtung'},
            {'type':'tile','entity':'light.desk','name':'Schreibtisch'},
            {'type':'custom:example','title':'Sonderkarte'}]}]})
        config=view_config({},model)
        self.assertEqual(config['labels'],{'light.desk':'Schreibtisch'})
        self.assertEqual(config['entities'],['light.desk'])
        markup=ui.dashboard(config,{'light.desk':{'state':'off','attributes':{}}},{'csrf':'test'},0,30)
        self.assertIn('Beleuchtung',markup);self.assertIn('Sonderkarte',markup)

    def test_cover_script_and_fan_cards_are_translated_without_arbitrary_actions(self):
        model=translate({'views':[{'cards':[
            {'type':'tile','entity':'cover.shade','grid_options':{'columns':3},'features':[{'type':'cover-open-close'}]},
            {'type':'tile','entity':'script.ventilate'}, {'type':'tile','entity':'fan.room'},
            {'type':'button','entity':'script.private','tap_action':{'action':'perform-action','perform_action':'script.unrelated'}}]}]})
        config=view_config({},model)
        self.assertEqual(model['control_entities'],['cover.shade','script.ventilate','fan.room'])
        self.assertEqual(config['columns']['cover.shade'],3)
        self.assertEqual(config['columns']['script.ventilate'],6)
        self.assertTrue(config['read_only']['script.private'])
        self.assertEqual(len(model['warnings']),1)

    def test_section_heading_stays_with_its_next_controls(self):
        cards=[{'type':'climate','entity':'climate.c','columns':12,'width_set':True},
            {'type':'climate','entity':'climate.a','columns':12,'width_set':True},
            {'type':'climate','entity':'climate.b','columns':12,'width_set':True},
            {'type':'climate','entity':'climate.d','columns':12,'width_set':True},
            {'type':'heading','name':'Next room'},
            {'type':'entity','entity':'script.room','columns':6,'read_only':False}]
        pages=ui.dashboard_pages(cards)
        self.assertGreaterEqual(len(pages),2)
        location=next(i for i,page in enumerate(pages) if any(c.get('name')=='Next room' for c in page))
        self.assertIn('script.room',[c.get('entity') for c in pages[location]])

    def test_user_arranged_room_fits_one_page_and_preserves_cover_order(self):
        raw={'views':[{'badges':['sensor.temp','sensor.humidity','binary_sensor.door','binary_sensor.window','sensor.clock'],'type':'sections','sections':[
            {'type':'grid','cards':[{'type':'thermostat','entity':'climate.room','grid_options':{'columns':6,'rows':4}},
                {'type':'tile','entity':'cover.window'}, {'type':'tile','entity':'cover.door'},
                *[{'type':'tile','entity':'light.'+name} for name in ('tv','sofa','ambient','ceiling','desk','bed')]]},
            {'type':'grid','cards':[{'type':'heading','heading':'Alcove'},
                {'type':'tile','entity':'fan.alcove'},{'type':'tile','entity':'script.alcove'},
                {'type':'tile','entity':'cover.alcove'},{'type':'tile','entity':'cover.roof'}]}]}]}
        config=view_config({},translate(raw));pages=ui.dashboard_layout_pages(ui.dashboard_cards(config))
        self.assertEqual(len(pages),1)
        grid=next(block for block in pages[0] if block['kind']=='grid')
        placed={p['card']['entity']:p for p in grid['placements']}
        self.assertEqual((placed['climate.room']['column'],placed['climate.room']['span'],placed['climate.room']['units']),(0,2,4))
        self.assertEqual((placed['cover.window']['row'],placed['cover.window']['column']),(0,2))
        self.assertEqual((placed['cover.door']['row'],placed['cover.door']['column']),(2,2))
        self.assertEqual((placed['light.tv']['row'],placed['light.sofa']['row']),(4,4))
        rendered=[c['entity'] for block in pages[0] for c in block['cards'] if 'entity' in c]
        self.assertEqual(set(rendered),set(config['entities']));self.assertEqual(len(rendered),len(set(rendered)))
        markup=ui.dashboard(config,{}, {'csrf':'test'},0,30)
        self.assertIn('grid-card grid-y-0 grid-n-4',markup)
        self.assertNotIn('rowspan=',markup)
        self.assertNotIn('<h1',markup)
        self.assertLess(markup.index('id="e-sensor-temp-value"'),markup.index('class="dashboard-grid"'))
        self.assertIn('class="climate-info"',markup)
        self.assertNotIn('class="mode-status"',markup)
        self.assertNotIn('class="climate-more"',markup)
        self.assertNotIn('class="pager"',markup)
        self.assertEqual(ui.label(config,'fan.alcove',{'attributes':{'friendly_name':'Alcove Fan'}}),'Alcove Fan')

    def test_large_grid_keeps_badges_with_cards_and_same_page_size_budget(self):
        config=view_config({},translate({'views':[{'badges':['sensor.temp'],'cards':[
            {'type':'tile','entity':'light.test'+str(i),'grid_options':{'columns':6}} for i in range(32)]}]}))
        pages=ui.dashboard_layout_pages(ui.dashboard_cards(config))
        self.assertGreater(len(pages),1)
        self.assertTrue(any(block['kind']=='grid' for block in pages[0]))
        import re
        budgets=[]
        for index in range(len(pages)):
            markup=ui.dashboard(config,{}, {'csrf':'test'},index,30)
            budgets.append(re.search(r'data-fit-rows="(\d+)"',markup).group(1))
            self.assertIn('class="pagination"',markup)
            self.assertNotIn('class="bottom-table"',markup)
            self.assertNotIn('%;width:',markup)
        self.assertEqual(len(set(budgets)),1)

    def test_ha_editor_script_actions_start_only_the_same_script_without_arguments(self):
        for action in ({'action':'perform-action','perform_action':'script.room','target':{}},
            {'action':'perform-action','perform_action':'script.turn_on','target':{'entity_id':['script.room']}}):
            model=translate({'views':[{'cards':[{'type':'tile','entity':'script.room','tap_action':action}]}]})
            config=view_config({},model)
            self.assertFalse(config['read_only']['script.room'])
            self.assertEqual(ui.card_units(ui.dashboard_cards(config)[0]),1)
            self.assertEqual(model['control_entities'],['script.room'])
        for action in ({'action':'perform-action','perform_action':'script.other'},
            {'action':'perform-action','perform_action':'script.room','data':{'private_argument':True}},
            {'action':'perform-action','perform_action':'script.turn_on','target':{'entity_id':['script.room','script.other']}}):
            model=translate({'views':[{'cards':[{'type':'tile','entity':'script.room','tap_action':action}]}]})
            self.assertEqual(model['control_entities'],[])

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
