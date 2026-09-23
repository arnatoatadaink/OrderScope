"""Loader for the reviewed A0-002 source manifest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from orderscope_local.contracts import ContractViolation
from .validation import A0ValidationWindows, SeriesMeasure, SeriesRole, SeriesSpec


SOURCE_MANIFEST_SCHEMA_VERSION = "a0-002-source-manifest-v0.1"


@dataclass(frozen=True, slots=True)
class A0SourceManifest:
    schema_version: str
    validation_case: str
    windows: A0ValidationWindows
    series: tuple[SeriesSpec, ...]
    unresolved_optional: tuple[tuple[SeriesRole, SeriesMeasure], ...]


def load_source_manifest(path: Path) -> A0SourceManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractViolation("A0-002 source manifest must be readable JSON") from exc
    if not isinstance(raw, dict):
        raise ContractViolation("A0-002 source manifest root must be an object")
    if raw.get("schema_version") != SOURCE_MANIFEST_SCHEMA_VERSION:
        raise ContractViolation("unsupported A0-002 source manifest schema version")
    validation_case = raw.get("validation_case")
    if not isinstance(validation_case, str) or not validation_case.strip():
        raise ContractViolation("validation_case must be non-empty text")

    windows = A0ValidationWindows(
        baseline_start=_timestamp(raw, "baseline_window", "start"),
        baseline_end=_timestamp(raw, "baseline_window", "end"),
        primary_start=_timestamp(raw, "primary_window", "start"),
        primary_end=_timestamp(raw, "primary_window", "end"),
    )

    items = raw.get("series")
    if not isinstance(items, list):
        raise ContractViolation("series must be a list")
    series: list[SeriesSpec] = []
    for item in items:
        if not isinstance(item, dict):
            raise ContractViolation("series entries must be objects")
        try:
            series.append(
                SeriesSpec(
                    role=SeriesRole(item["role"]),
                    measure=SeriesMeasure(item["measure"]),
                    series_id=item["series_id"],
                    source_ref=item["source_ref"],
                    unit=item["unit"],
                    timezone=item["timezone"],
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise ContractViolation("invalid A0-002 series manifest entry") from exc

    optional = raw.get("optional_series", [])
    if not isinstance(optional, list):
        raise ContractViolation("optional_series must be a list")
    unresolved: list[tuple[SeriesRole, SeriesMeasure]] = []
    for item in optional:
        if not isinstance(item, dict) or item.get("status") != "provider_unresolved":
            raise ContractViolation("optional series must be explicitly provider_unresolved")
        try:
            unresolved.append((SeriesRole(item["role"]), SeriesMeasure(item["measure"])))
        except (KeyError, ValueError, TypeError) as exc:
            raise ContractViolation("invalid optional A0-002 series manifest entry") from exc

    return A0SourceManifest(
        schema_version=SOURCE_MANIFEST_SCHEMA_VERSION,
        validation_case=validation_case,
        windows=windows,
        series=tuple(series),
        unresolved_optional=tuple(unresolved),
    )


def _timestamp(raw: dict[str, object], section: str, field: str) -> datetime:
    value = raw.get(section)
    if not isinstance(value, dict) or not isinstance(value.get(field), str):
        raise ContractViolation(f"{section}.{field} must be ISO-8601 text")
    try:
        return datetime.fromisoformat(value[field].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractViolation(f"{section}.{field} must be ISO-8601 text") from exc
