"""Pure normalization of Home Assistant dashboard gesture actions.

This module only describes actions. It never dispatches them.
"""
import copy
import re
from urllib.parse import urlsplit

SERVICE_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
GESTURES = {
    "tap": "tap_action",
    "icon": "icon_tap_action",
    "hold": "hold_action",
    "double_tap": "double_tap_action",
}
EXTENDED_GESTURES = {
    "icon_hold": "icon_hold_action",
    "icon_double_tap": "icon_double_tap_action",
}


def _descriptor(kind, explicit, **values):
    return {"kind": kind, "explicit": explicit, **values}


def _safe_navigation_path(value):
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//"):
        return False
    if "\\" in value or any(ord(char) < 32 for char in value):
        return False
    parts = urlsplit(value)
    return not parts.scheme and not parts.netloc


def _safe_url(value):
    if not isinstance(value, str) or value.strip()!=value or '\\' in value or any(ord(char)<32 for char in value):
        return False
    try:
        parts = urlsplit(value)
        parts.port  # Validate a malformed port without exposing the URL.
        return (parts.scheme.lower() in {"http", "https"} and bool(parts.netloc)
                and not parts.username and not parts.password)
    except ValueError:
        return False


def _normalize(raw, entity, gesture):
    if raw is None:
        return _descriptor("default", False)
    if not isinstance(raw, dict):
        return _descriptor("unsupported", True, reason="invalid_action_config")

    config = copy.deepcopy(raw)
    action = config.get("action")
    if not isinstance(action, str):
        return _descriptor("unsupported", True, reason="missing_action", metadata=config)

    result = {"explicit": True}
    if "confirmation" in config:
        result["confirmation"] = config["confirmation"]
    if gesture in {"hold", "double_tap"}:
        result["gesture"] = gesture

    if action in {"none", "toggle"}:
        result["kind"] = action
        return result
    if action == "more-info":
        result["kind"] = action
        result["entity"] = config.get("entity") or entity
        return result
    if action == "navigate":
        path = config.get("navigation_path")
        if not _safe_navigation_path(path):
            return {**result, "kind": "unsupported", "reason": "invalid_navigation_path", "metadata": config}
        result.update(kind="navigate", navigation_path=path)
        if "navigation_replace" in config:
            result["navigation_replace"] = config["navigation_replace"]
        return result
    if action == "url":
        path = config.get("url_path")
        if not _safe_url(path):
            return {**result, "kind": "unsupported", "reason": "invalid_url", "metadata": config}
        return {**result, "kind": "url", "url_path": path}
    if action in {"perform-action", "call-service"}:
        service = config.get("perform_action") if action == "perform-action" else config.get("service")
        if not isinstance(service, str) or not SERVICE_RE.fullmatch(service):
            return {**result, "kind": "unsupported", "reason": "invalid_service", "metadata": config}
        result.update(kind="service", service=service, source_action=action)
        data_key = "data" if "data" in config else "service_data"
        if data_key in config:
            result["data"] = copy.deepcopy(config[data_key])
        if "target" in config:
            result["target"] = copy.deepcopy(config["target"])
        return result
    return {**result, "kind": "unsupported", "reason": "unknown_action", "metadata": config}


def normalize_actions(card, entity):
    """Return inert descriptors for tap/icon/hold/double-tap actions.

    Missing tap and icon actions intentionally remain ``kind='default'`` so
    callers can preserve existing device-specific touch behavior.
    """
    card = card if isinstance(card, dict) else {}
    result = {name: _normalize(card.get(key), entity, name) for name, key in GESTURES.items()}
    result["extended_gestures"] = {
        name: {"kind": "unsupported", "explicit": True, "reason": "gesture_not_supported",
               "metadata": copy.deepcopy(card[key])}
        for name, key in EXTENDED_GESTURES.items()
        if key in card
    }
    result["warnings"] = warnings(card, result)
    return result


def warnings(card, actions):
    """Return notices for unsupported or semantically risky actions."""
    notices = []
    for gesture in actions.get("extended_gestures", {}):
        notices.append(f"{gesture}: gesture behavior is retained as unsupported metadata")
    for gesture in GESTURES:
        item = actions.get(gesture, {})
        if item.get("kind") == "unsupported":
            notices.append(f"{gesture}: {item.get('reason', 'unsupported')}")
        elif item.get("kind") == "service":
            notices.append(f"{gesture}: service action is metadata only; no dispatch")
        if item.get("confirmation"):
            notices.append(f"{gesture}: confirmation is retained as metadata, not implemented")
        if gesture in {"hold", "double_tap", "icon"} and item.get("kind") not in {"default", "unsupported"}:
            notices.append(f"{gesture}: gesture behavior requires separate UI support")
    return notices
