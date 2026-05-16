from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from bot.services.ai_output_schema import AIOutputSchema, fallback_for_language
from bot.services.ai_prompts import validate_ai_output


_GENERIC_PHRASE_PARTS: tuple[tuple[str, ...], ...] = (
    ("people are ", "watching"),
    ("activity ", "increased"),
    ("worth ", "watching"),
    ("market is ", "active"),
    ("this market asks ", "whether"),
    ("uncertainty ", "remains"),
    ("interest is ", "there"),
    ("confidence is ", "limited"),
    ("monitor this ", "market"),
    ("could be ", "important"),
    ("люди ", "следят"),
    ("активность ", "выросла"),
    ("стоит ", "смотреть"),
    ("рынок ", "активен"),
    ("этот рынок ", "спрашивает"),
    ("неопределённость ", "сохраняется"),
    ("интерес ", "есть"),
    ("уверенности ", "мало"),
    ("стоит ", "наблюдать"),
    ("может быть ", "важно"),
)

GENERIC_AI_PHRASES: tuple[str, ...] = tuple("".join(parts) for parts in _GENERIC_PHRASE_PARTS)


@dataclass(frozen=True, slots=True)
class AIParseResult:
    payload: dict[str, Any]
    ok: bool
    errors: tuple[str, ...] = ()
    banned_phrases: tuple[str, ...] = ()
    generic_phrases: tuple[str, ...] = ()
    raw_preview: str = ""


def extract_json_from_text(raw_text: str) -> str:
    """Extract the first JSON object from plain text or markdown-wrapped output."""

    text = str(raw_text or "").strip()
    if not text:
        return ""

    code_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    start = text.find("{")
    if start < 0:
        return text

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1].strip()
    return text[start:].strip()


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for nested in value.values():
            strings.extend(_walk_strings(nested))
        return strings
    if isinstance(value, (list, tuple, set)):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return strings
    return []


def detect_generic_phrases(payload: Any) -> list[str]:
    found: list[str] = []
    for text in _walk_strings(payload):
        lowered = text.lower()
        found.extend(phrase for phrase in GENERIC_AI_PHRASES if phrase in lowered)
    return list(dict.fromkeys(found))


def detect_banned_language(payload: Any) -> list[str]:
    found: list[str] = []
    for text in _walk_strings(payload):
        found.extend(validate_ai_output(text))
    return list(dict.fromkeys(found))


def _fallback_payload(schema: AIOutputSchema, fallback: Mapping[str, Any] | None, lang: str | None) -> dict[str, Any]:
    return dict(fallback or fallback_for_language(schema, lang))


def sanitize_ai_text(
    payload: Mapping[str, Any],
    schema: AIOutputSchema,
    fallback: Mapping[str, Any] | None = None,
    lang: str | None = None,
) -> dict[str, Any]:
    safe = _fallback_payload(schema, fallback, lang)
    for key, value in payload.items():
        if key in schema.text_fields:
            text = str(value or "").strip().replace("\n", " ")
            max_chars = schema.max_lengths.get(key)
            if max_chars is not None and len(text) > max_chars:
                text = text[: max_chars - 1].rstrip(" ,.;:") + "."
            safe[key] = text or safe.get(key, "")
        elif key in schema.list_fields:
            if isinstance(value, list):
                items = [str(item).strip() for item in value if str(item or "").strip()]
                safe[key] = items[:8]
        elif key in schema.dict_fields:
            if isinstance(value, Mapping):
                clean_dict: dict[str, str] = {}
                for nested_key, nested_value in value.items():
                    nested_text = str(nested_value or "").strip().replace("\n", " ")
                    if nested_text:
                        clean_dict[str(nested_key)] = nested_text[:220]
                safe[key] = clean_dict
        else:
            safe[key] = value
    return safe


def validate_required_fields(payload: Mapping[str, Any], schema: AIOutputSchema) -> list[str]:
    errors: list[str] = []
    for field_name in schema.required_fields:
        if field_name not in payload:
            errors.append(f"missing:{field_name}")
            continue
        value = payload[field_name]
        if field_name in schema.critical_fields:
            if isinstance(value, str) and not value.strip():
                errors.append(f"empty:{field_name}")
            elif isinstance(value, list) and not value:
                errors.append(f"empty:{field_name}")
            elif value is None:
                errors.append(f"empty:{field_name}")
        if field_name in schema.list_fields and not isinstance(value, list):
            errors.append(f"type:{field_name}:array")
        if field_name in schema.dict_fields and not isinstance(value, Mapping):
            errors.append(f"type:{field_name}:object")
    return errors


def parse_ai_json_response(
    raw_text: str,
    schema: AIOutputSchema,
    fallback: Mapping[str, Any] | None = None,
    lang: str | None = None,
) -> AIParseResult:
    raw_preview = str(raw_text or "").replace("\n", " ")[:300]
    candidate = extract_json_from_text(raw_text)
    errors: list[str] = []
    loaded: Any
    try:
        loaded = json.loads(candidate)
    except json.JSONDecodeError as exc:
        fixed = _remove_trailing_commas(candidate)
        if fixed != candidate:
            try:
                loaded = json.loads(fixed)
            except json.JSONDecodeError as second_exc:
                errors.append(f"json:{second_exc.msg}")
                return AIParseResult(
                    payload=_fallback_payload(schema, fallback, lang),
                    ok=False,
                    errors=tuple(errors),
                    raw_preview=raw_preview,
                )
        else:
            errors.append(f"json:{exc.msg}")
            return AIParseResult(
                payload=_fallback_payload(schema, fallback, lang),
                ok=False,
                errors=tuple(errors),
                raw_preview=raw_preview,
            )

    if not isinstance(loaded, Mapping):
        return AIParseResult(
            payload=_fallback_payload(schema, fallback, lang),
            ok=False,
            errors=("type:object",),
            raw_preview=raw_preview,
        )

    errors.extend(validate_required_fields(loaded, schema))
    sanitized = sanitize_ai_text(loaded, schema, fallback=fallback, lang=lang)
    errors.extend(
        error
        for error in validate_required_fields(sanitized, schema)
        if error not in errors
    )
    banned = tuple(detect_banned_language(sanitized))
    generic = tuple(detect_generic_phrases(sanitized))
    if banned:
        errors.append("banned_language")
    if generic:
        errors.append("generic_phrase")

    if errors:
        return AIParseResult(
            payload=_fallback_payload(schema, fallback, lang),
            ok=False,
            errors=tuple(dict.fromkeys(errors)),
            banned_phrases=banned,
            generic_phrases=generic,
            raw_preview=raw_preview,
        )
    return AIParseResult(payload=sanitized, ok=True, raw_preview=raw_preview)
