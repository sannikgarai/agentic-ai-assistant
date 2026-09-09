"""
LLM response parsing utilities.

Provides safe parsing of normal text and JSON responses
returned by the LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


# ============================================================
# 1. PARSED RESPONSE
# ============================================================

@dataclass
class ParsedLLMResponse:
    """
    Normalized representation of an LLM response.
    """

    text: str
    data: dict[str, Any] | list[Any] | None = None
    is_json: bool = False


# ============================================================
# 2. REMOVE MARKDOWN CODE FENCES
# ============================================================

def remove_code_fences(text: str) -> str:
    """
    Remove Markdown code fences from an LLM response.
    """

    if not text:
        return ""

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json|JSON)?\s*",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    return cleaned.strip()


# ============================================================
# 3. EXTRACT JSON
# ============================================================

def extract_json(text: str) -> str:
    """
    Extract the first valid JSON object or array
    from an LLM response.
    """

    if not text or not text.strip():
        raise ValueError("LLM response is empty.")

    cleaned = remove_code_fences(text)

    # --------------------------------------------------------
    # Try the complete response first.
    # --------------------------------------------------------

    try:
        json.loads(cleaned)
        return cleaned

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Scan for valid JSON objects or arrays.
    # --------------------------------------------------------

    decoder = json.JSONDecoder()

    for match in re.finditer(
        r"[\[{]",
        cleaned,
    ):
        start = match.start()

        try:
            _, end = decoder.raw_decode(
                cleaned[start:]
            )

            candidate = cleaned[
                start:start + end
            ]

            json.loads(candidate)

            return candidate

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

    raise ValueError(
        "No valid JSON object or array found in LLM response."
    )


# ============================================================
# 4. PARSE JSON RESPONSE
# ============================================================

def parse_json_response(
    text: str,
) -> dict[str, Any] | list[Any]:
    """
    Parse an LLM response into a Python dictionary or list.
    """

    if not text or not text.strip():
        raise ValueError(
            "LLM response is empty."
        )

    json_text = extract_json(text)

    try:
        data = json.loads(json_text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid JSON returned by LLM."
        ) from exc

    if not isinstance(
        data,
        (dict, list),
    ):
        raise ValueError(
            "LLM JSON response must be an object or array."
        )

    return data


# ============================================================
# 5. PARSE GENERAL LLM RESPONSE
# ============================================================

def parse_llm_response(
    text: str,
) -> ParsedLLMResponse:
    """
    Parse a general LLM response.

    If valid JSON is detected:
    - data contains the parsed JSON.
    - is_json is True.

    Otherwise:
    - data is None.
    - is_json is False.
    """

    if not text or not text.strip():
        raise ValueError(
            "LLM response is empty."
        )

    cleaned = text.strip()

    try:
        data = parse_json_response(
            cleaned
        )

        return ParsedLLMResponse(
            text=cleaned,
            data=data,
            is_json=True,
        )

    except ValueError:
        return ParsedLLMResponse(
            text=cleaned,
            data=None,
            is_json=False,
        )


# ============================================================
# 6. GET REQUIRED FIELD
# ============================================================

def get_required_field(
    data: dict[str, Any],
    field: str,
) -> Any:
    """
    Retrieve a required field from parsed JSON.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Parsed JSON must be an object."
        )

    if field not in data:
        raise ValueError(
            f"Required field '{field}' is missing."
        )

    value = data[field]

    if value is None:
        raise ValueError(
            f"Required field '{field}' is null."
        )

    return value


# ============================================================
# 7. GET OPTIONAL FIELD
# ============================================================

def get_optional_field(
    data: dict[str, Any],
    field: str,
    default: Any = None,
) -> Any:
    """
    Retrieve an optional field from parsed JSON.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Parsed JSON must be an object."
        )

    return data.get(
        field,
        default,
    )