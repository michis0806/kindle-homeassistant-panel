import unittest

from dashboard_actions import normalize_actions


class DashboardActionsTests(unittest.TestCase):
    def test_missing_actions_remain_defaults(self):
        actions = normalize_actions({}, "light.kitchen")
        self.assertEqual(actions["tap"], {"kind": "default", "explicit": False})
        self.assertEqual(actions["icon"], {"kind": "default", "explicit": False})

    def test_basic_actions_and_more_info_fallback(self):
        actions = normalize_actions({
            "tap_action": {"action": "more-info"},
            "icon_tap_action": {"action": "toggle"},
            "hold_action": {"action": "none"},
        }, "light.kitchen")
        self.assertEqual(actions["tap"]["entity"], "light.kitchen")
        self.assertEqual(actions["icon"]["kind"], "toggle")
        self.assertEqual(actions["hold"]["kind"], "none")

    def test_navigation_requires_safe_relative_absolute_path(self):
        for path in ("//evil.example/x", "javascript:alert(1)", "https://evil.example", "relative/path", "/\\evil"):
            actions = normalize_actions({"tap_action": {"action": "navigate", "navigation_path": path}}, "sensor.temp")
            self.assertEqual(actions["tap"]["kind"], "unsupported", path)
        actions = normalize_actions({"tap_action": {"action": "navigate", "navigation_path": "/lovelace/kitchen"}}, "sensor.temp")
        self.assertEqual(actions["tap"]["kind"], "navigate")

    def test_url_requires_http_without_credentials(self):
        for path in ("javascript:alert(1)", "file:///etc/passwd", "https://user:pass@example.com/x", "https:///missing-host"):
            actions = normalize_actions({"tap_action": {"action": "url", "url_path": path}}, "sensor.temp")
            self.assertEqual(actions["tap"]["kind"], "unsupported", path)
        actions = normalize_actions({"tap_action": {"action": "url", "url_path": "https://example.com/x"}}, "sensor.temp")
        self.assertEqual(actions["tap"]["kind"], "url")

    def test_service_is_inert_metadata_and_keeps_data_target_confirmation(self):
        card = {"tap_action": {
            "action": "perform-action", "perform_action": "script.good_night",
            "data": {"mode": "quiet"}, "target": {"entity_id": "script.good_night"},
            "confirmation": {"text": "Sure?"},
        }}
        actions = normalize_actions(card, "script.good_night")
        self.assertEqual(actions["tap"]["kind"], "service")
        self.assertEqual(actions["tap"]["service"], "script.good_night")
        self.assertEqual(actions["tap"]["data"], {"mode": "quiet"})
        self.assertEqual(actions["tap"]["target"], {"entity_id": "script.good_night"})
        self.assertEqual(actions["tap"]["confirmation"], {"text": "Sure?"})
        self.assertTrue(any("metadata only" in warning for warning in actions["warnings"]))
        self.assertTrue(any("confirmation" in warning for warning in actions["warnings"]))

    def test_legacy_call_service_normalizes_but_never_dispatches(self):
        actions = normalize_actions({"tap_action": {"action": "call-service", "service": "light.turn_on", "service_data": {"entity_id": "light.kitchen"}}}, "light.kitchen")
        self.assertEqual(actions["tap"]["kind"], "service")
        self.assertEqual(actions["tap"]["data"], {"entity_id": "light.kitchen"})
        self.assertTrue(any("no dispatch" in warning for warning in actions["warnings"]))

    def test_service_shape_is_validated(self):
        actions = normalize_actions({"tap_action": {"action": "perform-action", "perform_action": "script;evil.run"}}, "script.good_night")
        self.assertEqual(actions["tap"]["kind"], "unsupported")
        self.assertEqual(actions["tap"]["reason"], "invalid_service")

    def test_matching_script_descriptor_is_inert(self):
        # Normalization describes the exact own-script shape but grants no
        # execution authority; dispatch belongs to a separate caller.
        actions = normalize_actions({"tap_action": {"action": "perform-action", "perform_action": "script.turn_on", "target": {"entity_id": "script.good_night"}}}, "script.good_night")
        self.assertEqual(actions["tap"]["kind"], "service")
        self.assertEqual(actions["tap"]["target"], {"entity_id": "script.good_night"})
        self.assertTrue(any("metadata only" in warning for warning in actions["warnings"]))

    def test_hold_double_tap_metadata_and_warnings(self):
        actions = normalize_actions({
            "hold_action": {"action": "toggle", "confirmation": True},
            "double_tap_action": {"action": "more-info"},
        }, "switch.plug")
        self.assertTrue(any("hold: gesture behavior" in warning for warning in actions["warnings"]))
        self.assertTrue(any("confirmation" in warning for warning in actions["warnings"]))
        self.assertEqual(actions["double_tap"]["kind"], "more-info")

    def test_extended_icon_gestures_are_retained_as_unsupported_metadata(self):
        config = {"icon_hold_action": {"action": "toggle"},
                  "icon_double_tap_action": {"action": "navigate", "navigation_path": "/lovelace/0"}}
        actions = normalize_actions(config, "light.kitchen")
        self.assertEqual(actions["extended_gestures"]["icon_hold"]["kind"], "unsupported")
        self.assertEqual(actions["extended_gestures"]["icon_hold"]["metadata"], config["icon_hold_action"])
        self.assertTrue(any("icon_hold" in warning for warning in actions["warnings"]))


if __name__ == "__main__":
    unittest.main()
