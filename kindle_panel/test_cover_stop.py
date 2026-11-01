import threading
import unittest

import ui
from server import App, digest


class CoverStopTests(unittest.TestCase):
    def test_three_controls_follow_feature_bits_and_stop_is_usable_when_supported(self):
        for features, expected_disabled in (
            (1, {'open_cover': False, 'stop_cover': True, 'close_cover': True}),
            (2, {'open_cover': True, 'stop_cover': True, 'close_cover': False}),
            (8, {'open_cover': True, 'stop_cover': False, 'close_cover': True}),
        ):
            with self.subTest(features=features):
                item = {'state': 'open', 'attributes': {'supported_features': features, 'current_position': 50}}
                markup = ui.cover_tile('cover.test', item, {'csrf': 'test'}, 0, {})
                ids = ['e-cover-test-open_cover', 'e-cover-test-stop_cover', 'e-cover-test-close_cover']
                self.assertEqual([markup.index(button_id) for button_id in ids], sorted(markup.index(button_id) for button_id in ids))
                self.assertIn('aria-label="Stopp"', markup)
                self.assertIn('>■</button>', markup)
                for action, disabled in expected_disabled.items():
                    button_id = 'e-cover-test-' + action
                    button = markup[markup.index(button_id):]
                    button = button[:button.index('</button>')]
                    self.assertEqual(' disabled' in button, disabled, action)

                config = {'entities': ['cover.test']}
                patches = {patch['id']: patch for patch in ui.updates(config, {'cover.test': item})['patches']}
                self.assertEqual(patches['e-cover-test-stop_cover']['disabled'], features != 8)

    def test_server_dispatches_stop_only_when_feature_is_supported(self):
        states = {'cover.test': {'entity_id': 'cover.test', 'state': 'open', 'attributes': {'supported_features': 8}}}
        calls = []

        def api(path, payload):
            if path == 'states':
                return list(states.values())
            calls.append((path, payload))
            return []

        app = object.__new__(App)
        app.lock = threading.RLock()
        app.panel_lock = threading.RLock()
        app.panel_cache = None
        token = 'a' * 64
        device = {'approved': True, 'csrf': 'test-csrf'}
        app.data = {'entities': ['cover.test'], 'devices': {digest(token): device}}
        app.dashboard_source = None
        app.api = lambda path, payload=None: api(path, payload)

        app.control(token, device['csrf'], 'cover.test', 'stop_cover')
        self.assertEqual(calls, [('services/cover/stop_cover', {'entity_id': 'cover.test'})])
        states['cover.test']['attributes']['supported_features'] = 2
        with self.assertRaises(ValueError):
            app.control(token, device['csrf'], 'cover.test', 'stop_cover')
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
