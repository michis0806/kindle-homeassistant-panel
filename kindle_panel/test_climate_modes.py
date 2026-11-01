import unittest
import threading

import ui
from ha_dashboard import translate, view_config
from server import App


class ClimateModeRestrictionTests(unittest.TestCase):
    def setUp(self):
        self.supported=['off','fan_only','dry','cool','heat','heat_cool','auto']
        self.states={'climate.room':{'entity_id':'climate.room','state':'off','attributes':{
            'supported_features':0,'hvac_modes':list(self.supported)}}}

    def config(self, features_marker=...):
        card={'type':'thermostat','entity':'climate.room'}
        if features_marker is not ...:
            card['features']=[{'type':'climate-hvac-modes','hvac_modes':features_marker}]
        return view_config({},translate({'views':[{'cards':[card]}]}))

    def test_missing_feature_modes_keeps_all_entity_modes(self):
        config=self.config()
        self.assertNotIn('climate.room',config['climate_modes'])
        markup=ui.climate_panel(config,'climate.room',self.states['climate.room'],{'csrf':'x'})
        for mode in self.supported:self.assertIn('mode-'+mode+'"',markup)

    def test_explicit_subset_is_intersected_and_displayed_in_supported_order(self):
        config=self.config(['heat','nonsense','off','heat'])
        self.assertEqual(config['climate_modes']['climate.room'],['off','heat'])
        markup=ui.climate_panel(config,'climate.room',self.states['climate.room'],{'csrf':'x'})
        self.assertIn('mode-off"',markup);self.assertIn('mode-heat"',markup)
        self.assertNotIn('mode-cool"',markup);self.assertNotIn('mode-nonsense"',markup)
        patches=ui.updates(config,self.states)['patches']
        disabled={p['id']:p['disabled'] for p in patches if '-mode-' in p['id']}
        self.assertFalse(disabled['e-climate-room-mode-off'])
        self.assertTrue(disabled['e-climate-room-mode-cool'])

    def test_explicit_empty_subset_disables_every_mode(self):
        config=self.config([])
        self.assertEqual(config['climate_modes']['climate.room'],[])
        markup=ui.climate_panel(config,'climate.room',self.states['climate.room'],{'csrf':'x'})
        self.assertNotIn('mode-off"',markup)
        patches=ui.updates(config,self.states)['patches']
        self.assertTrue(all(p['disabled'] for p in patches if '-mode-' in p['id']))

    def test_posted_mode_must_be_allowed_by_assigned_view(self):
        calls=[];token='device-token';device={'approved':True,'csrf':'csrf'}
        app=App.__new__(App)
        app.panel_lock=threading.RLock();app.panel_cache=None
        app.device=lambda value:device
        app.states=lambda:self.states
        app.render_config=lambda value:{'entities':['climate.room'],'control_entities':['climate.room'],
            'climate_modes':{'climate.room':['heat']}}
        app.api=lambda path,payload:calls.append((path,payload))
        with self.assertRaises(ValueError):
            app.control(token,'csrf','climate.room','climate_hvac','cool')
        self.assertEqual(calls,[])
        app.control(token,'csrf','climate.room','climate_hvac','heat')
        self.assertEqual(calls,[('services/climate/set_hvac_mode',{'entity_id':'climate.room','hvac_mode':'heat'})])


if __name__=='__main__':
    unittest.main()
