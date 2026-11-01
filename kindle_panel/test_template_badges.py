import unittest
import ha_dashboard
import template_badges
import ui

class TemplateBadgeTests(unittest.TestCase):
    def config(self, **values):
        badge=dict(type='custom:mushroom-template-badge',content="{{ now().strftime('%H:%M') }}",icon='mdi:clock',**values)
        return ha_dashboard.view_config({},ha_dashboard.translate({'views':[{'path':'room','badges':[badge]}]}))

    def test_clock_badge_without_entity_and_partial_text_updates(self):
        config=self.config();calls=[];clock=[0];value=['16:05']
        def api(path,payload):calls.append((path,payload));return value[0]
        renderer=template_badges.Renderer(api,lambda:clock[0])
        config['template_values']=renderer.values(config)
        html=ui.dashboard(config,{}, {'csrf':'test'},0,30)
        self.assertEqual(config['entities'],[])
        self.assertIn('16:05',html);self.assertNotIn('{{ now()',html)
        self.assertIn('badge-icon',html);self.assertNotIn('Nicht unterstütztes Badge',html)
        patches=ui.updates(config,{})['patches'];self.assertEqual(patches[0]['text'],'16:05')
        self.assertEqual(calls[0][0],'template')
        clock[0]=9;value[0]='16:06';self.assertEqual(renderer.values(config),config['template_values'])
        clock[0]=10;config['template_values']=renderer.values(config)
        self.assertEqual(ui.updates(config,{})['patches'][0]['text'],'16:06')
        self.assertEqual(len(calls),2)

    def test_home_assistant_variables_and_escaped_content(self):
        config=self.config(entity='sensor.test',area='nursery',label='Room')
        calls=[]
        def api(path,payload):calls.append(payload);return '<script>bad</script>'
        config['template_values']=template_badges.Renderer(api).values(config)
        self.assertEqual(calls[0]['variables'],{'entity':'sensor.test','area':'nursery'})
        markup=ui.dashboard(config,{}, {'csrf':'test'},0,30)
        self.assertIn('&lt;script&gt;bad&lt;/script&gt;',markup)
        self.assertNotIn('<script>bad</script>',markup)
        self.assertIn('Room',markup)

    def test_template_failure_isolated_and_retried(self):
        config=self.config();clock=[0];calls=[]
        def api(path,payload):calls.append(path);raise RuntimeError('offline')
        renderer=template_badges.Renderer(api,lambda:clock[0])
        values=renderer.values(config);self.assertEqual(next(iter(values.values()))['content'],'—')
        renderer.values(config);self.assertEqual(len(calls),1)
        clock[0]=10;renderer.values(config);self.assertEqual(len(calls),2)

    def test_template_actions_are_not_promoted_to_entity_controls(self):
        model=ha_dashboard.translate({'views':[{'badges':[{'type':'custom:mushroom-template-badge','entity':'light.private','content':'Clock','tap_action':{'action':'toggle'}}]}]})
        self.assertEqual(model['entities'],[]);self.assertEqual(model['control_entities'],[])
        self.assertTrue(any('Aktionen' in warning for warning in model['warnings']))

if __name__=='__main__':unittest.main()
