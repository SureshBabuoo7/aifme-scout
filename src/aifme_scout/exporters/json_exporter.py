"""JSON Exporter for ScoutSchema.

Serializes a ScoutSchema into a stable, pretty-printed JSON document that
conforms to schemas/v1/scan-result.schema.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from aifme_scout.extractors.models import ScoutSchema


def _to_serializable(value: Any) -> Any:
    """Recursively convert a value to a JSON-serializable form.

    Args:
        value: The value to convert.

    Returns:
        A JSON-serializable representation of the value.
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list):
        return [_to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}
    if is_dataclass(value):
        return _to_serializable(asdict(value))  # type: ignore[arg-type]
    return str(value)


def export(schema: ScoutSchema) -> str:
    """Serialize a ScoutSchema to a pretty-printed JSON string.

    The output is UTF-8 encoded, pretty-printed with 2-space indentation,
    and uses stable alphabetical key ordering for deterministic output.

    Args:
        schema: The ScoutSchema to serialize.

    Returns:
        A UTF-8 encoded, pretty-printed JSON string with stable key ordering.

    Raises:
        TypeError: If the schema contains values that cannot be serialized to
            JSON.
    """
    data = _to_serializable(asdict(schema))
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)


def export_to_file(schema: ScoutSchema, path: str | Path) -> None:
    """Serialize a ScoutSchema and write it to a file.

    Args:
        schema: The ScoutSchema to serialize.
        path: File path to write the JSON output to.

    Raises:
        OSError: If the file cannot be written.
        TypeError: If the schema cannot be serialized to JSON.
    """
    content = export(schema)
    Path(path).write_text(content, encoding="utf-8")
