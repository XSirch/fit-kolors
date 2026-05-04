import copy
import re

from config import API_VERSION


VALID_PHOTO_FLAGS = {
    "low_light",
    "heavy_filter",
    "face_not_centered",
    "wearing_sunglasses",
    "heavy_makeup",
    "multiple_faces",
    "no_face_detected",
}


HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def normalize_analysis_response(raw_response, api_version=API_VERSION):
    payload = copy.deepcopy(raw_response or {})

    payload["model_version"] = api_version

    payload["confidence"] = _normalize_confidence(
        _first_present(
            _pick(payload, "confidence"),
            _pick(payload.get("analysis"), "confidence"),
            _pick(payload.get("quality"), "confidence"),
        )
    )
    payload["photo_flags"] = _normalize_photo_flags(
        _first_present(
            _pick(payload, "photo_flags"),
            _pick(payload.get("quality"), "photo_flags"),
            _pick(payload.get("analysis"), "photo_flags"),
        )
    )

    payload["detected_colors"] = _normalize_detected_colors(
        payload.get("detected_colors") or {}
    )
    payload["analysis"] = _normalize_analysis(payload.get("analysis") or {})
    payload["recommendations"] = _normalize_recommendations(
        payload.get("recommendations") or {}
    )
    payload["makeup_tips"] = _normalize_makeup_tips(payload.get("makeup_tips") or {})
    payload["makeup"] = _normalize_makeup(payload.get("makeup") or {})
    payload["hair"] = _normalize_hair(payload.get("hair") or {})
    payload["colors_to_avoid"] = _normalize_colors_to_avoid(
        payload.get("colors_to_avoid") or []
    )

    return payload


def _pick(mapping, *keys):
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def _first_present(*values):
    for value in values:
        if value is not None:
            return value
    return None


def _string_value(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def _normalize_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0

    if confidence > 1:
        confidence = confidence / 100
    return max(0.0, min(confidence, 1.0))


def _normalize_photo_flags(value):
    if not isinstance(value, list):
        return []
    return [flag for flag in value if flag in VALID_PHOTO_FLAGS]


def _normalize_hex(value):
    if value is None:
        return ""
    color = str(value).strip()
    if not color:
        return ""
    if not color.startswith("#"):
        color = f"#{color}"
    if HEX_RE.match(color):
        return color.upper()
    return color


def _normalize_hex_list(value):
    if not isinstance(value, list):
        return []
    return [_normalize_hex(item) for item in value if _normalize_hex(item)]


def _normalize_detected_colors(colors):
    return {
        "skin": _normalize_hex(_pick(colors, "skin")),
        "hair": _normalize_hex(_pick(colors, "hair")),
        "eyes": _normalize_hex(_pick(colors, "eyes")),
        "lips": _normalize_hex(_pick(colors, "lips")),
    }


def _normalize_analysis(analysis):
    return {
        "season": _string_value(_pick(analysis, "season")),
        "undertone": _string_value(_pick(analysis, "undertone")),
        "contrast": _string_value(_pick(analysis, "contrast")),
        "depth": _string_value(_pick(analysis, "depth", "profundidade")),
        "metals": _normalize_string_list(_pick(analysis, "metals")),
        "explanation": _string_value(_pick(analysis, "explanation")),
    }


def _normalize_string_list(value):
    if isinstance(value, list):
        return [_string_value(item) for item in value if _string_value(item)]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _normalize_recommendations(recommendations):
    normalized = {}
    for season, palette in recommendations.items():
        if not isinstance(palette, dict):
            continue
        normalized[season] = {
            "theory": _string_value(_pick(palette, "theory", "teoria")),
            "day": _normalize_hex_list(_pick(palette, "day", "dia")),
            "night": _normalize_hex_list(_pick(palette, "night", "noite")),
        }
    return normalized


def _normalize_makeup_tips(makeup_tips):
    return {
        "lipstick": _string_value(_pick(makeup_tips, "lipstick", "batom")),
        "blush": _string_value(_pick(makeup_tips, "blush")),
        "eyeshadow": _string_value(_pick(makeup_tips, "eyeshadow", "sombras")),
    }


def _normalize_makeup(makeup):
    return {
        "lipstick": _normalize_hex_list(_pick(makeup, "lipstick", "batom")),
        "blush": _normalize_hex_list(_pick(makeup, "blush")),
        "eyeshadow": _normalize_hex_list(_pick(makeup, "eyeshadow", "sombras")),
        "foundation_undertone": _string_value(
            _pick(makeup, "foundation_undertone", "foundationUndertone", "base")
        ),
    }


def _normalize_hair(hair):
    return {
        "recommended_tones": _normalize_hex_list(
            _pick(hair, "recommended_tones", "recommendedTones", "tons")
        ),
        "highlights": _normalize_hex_list(_pick(hair, "highlights", "luzes")),
        "notes": _string_value(_pick(hair, "notes", "observacoes")),
    }


def _normalize_colors_to_avoid(colors_to_avoid):
    if not isinstance(colors_to_avoid, list):
        return []

    normalized = []
    for item in colors_to_avoid:
        if not isinstance(item, dict):
            continue
        color = _normalize_hex(_pick(item, "hex", "color", "value"))
        reason = _string_value(_pick(item, "reason", "motivo"))
        if color and reason:
            normalized.append({"hex": color, "reason": reason})
    return normalized
