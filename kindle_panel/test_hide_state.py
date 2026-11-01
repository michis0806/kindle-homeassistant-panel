import unittest

import ha_dashboard
import ui


class HideCoverStateTests(unittest.TestCase):
    def config(self, hide_state_marker=...):
        card = {'type': 'tile', 'entity': 'cover.shade'}
        if hide_state_marker is not ...:
            card['hide_state'] = hide_state_marker
        model = ha_dashboard.translate({'views': [{'path': 'room', 'cards': [card]}]})
        return ha_dashboard.view_config({}, model)

    def render(self, config, state='open'):
        item = {'state': state, 'attributes': {'supported_features': 3, 'current_position': 100}}
        return ui.dashboard(config, {'cover.shade': item}, {'csrf': 'test'}, 0, 30)

    def test_hidden_cover_state_omits_status_but_keeps_controls_and_live_disabling(self):
        config = self.config(True)
        markup = self.render(config)

        self.assertTrue(config['presentation']['cover.shade']['hide_state'])
        self.assertIn('class="cover-inner hide-state"', markup)
        self.assertNotIn('class="cover-state"', markup)
        self.assertNotIn('id="e-cover-shade-cover-status"', markup)
        self.assertNotIn('Geschlossen', markup)
        self.assertIn('id="e-cover-shade-open_cover"', markup)
        self.assertIn('id="e-cover-shade-close_cover"', markup)
        self.assertIn('id="e-cover-shade-open_cover" aria-label="Öffnen" disabled', markup)
        self.assertNotIn('id="e-cover-shade-close_cover" aria-label="Schließen" disabled', markup)

        patches = {patch['id']: patch for patch in ui.updates(config, {'cover.shade': {
            'state': 'open', 'attributes': {'supported_features': 3, 'current_position': 100}}})['patches']}
        self.assertTrue(patches['e-cover-shade-open_cover']['disabled'])
        self.assertFalse(patches['e-cover-shade-close_cover']['disabled'])

    def test_default_cover_keeps_status(self):
        markup = self.render(self.config())
        self.assertIn('class="cover-inner"', markup)
        self.assertIn('class="cover-state"', markup)
        self.assertIn('Offen · 100 %', markup)


if __name__ == '__main__':
    unittest.main()
