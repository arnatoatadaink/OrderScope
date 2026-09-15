from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path

from orderscope_local.cross_market import load_source_manifest
from orderscope_local.cross_market.official_macro import collect_official_macro
from orderscope_local.cross_market.validation import SeriesMeasure, SeriesObservation, SeriesRole


MANIFEST = Path("analysis/config/cross_market/a0-002-sources-v0.1.json")
ALPACA_INPUT = Path("var/cross-market/a0-002/alpaca-daily-observations.json")
MACRO_OUTPUT = Path("var/cross-market/a0-002/official-macro-observations.json")
COMBINED_OUTPUT = Path("var/cross-market/a0-002/a0-002-observations.json")


def main() -> None:
    manifest = load_source_manifest(MANIFEST)
    start = manifest.windows.baseline_start.date()
    end_exclusive = manifest.windows.primary_end.date()

    macro = collect_official_macro(start=start, end_exclusive=end_exclusive)
    _validate_manifest_refs(manifest.series, macro)
    _write_observation_file(
        MACRO_OUTPUT,
        schema_version="a0-002-official-macro-observations-v0.1",
        validation_case=manifest.validation_case,
        start=start,
        end_exclusive=end_exclusive,
        observations=macro,
    )

    alpaca = _read_observation_file(ALPACA_INPUT)
    combined = tuple(sorted((*alpaca, *macro), key=lambda item: (item.analysis_date, item.role.value, item.measure.value)))
    _validate_manifest_refs(manifest.series, combined)

    expected = {(spec.role, spec.measure) for spec in manifest.series}
    observed = {(item.role, item.measure) for item in combined}
    missing = expected - observed
    if missing:
        names = sorted(f"{role.value}:{measure.value}" for role, measure in missing)
        raise RuntimeError(f"A0-002 required series are missing observations: {names}")

    _write_observation_file(
        COMBINED_OUTPUT,
        schema_version="a0-002-combined-observations-v0.1",
        validation_case=manifest.validation_case,
        start=start,
        end_exclusive=end_exclusive,
        observations=combined,
    )

    print(f"macro_output       = {MACRO_OUTPUT}")
    print(f"macro_count        = {len(macro)}")
    print(f"combined_output    = {COMBINED_OUTPUT}")
    print(f"combined_count     = {len(combined)}")
    print(f"required_series    = {len(expected)}/{len(expected)}")
    print("A0-002 official macro collection + merge = PASS")


def _validate_manifest_refs(specs, observations: tuple[SeriesObservation, ...]) -> None:
    expected = {(spec.role, spec.measure): spec.source_ref for spec in specs}
    for item in observations:
        key = (item.role, item.measure)
        if key not in expected:
            raise RuntimeError(f"A0-002 observation is not registered in manifest: {item.role.value}:{item.measure.value}")
        if expected[key] != item.source_ref:
            raise RuntimeError(f"A0-002 source_ref drift: {item.role.value}:{item.measure.value}")


def _read_observation_file(path: Path) -> tuple[SeriesObservation, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("observations")
    if not isinstance(rows, list):
        raise RuntimeError(f"invalid A0-002 observation file: {path}")
    result: list[SeriesObservation] = []
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError(f"invalid observation row in {path}")
        result.append(
            SeriesObservation(
                role=SeriesRole(row["role"]),
                measure=SeriesMeasure(row["measure"]),
                analysis_date=date.fromisoformat(row["analysis_date"]),
                observed_at=_timestamp(row["observed_at"]),
                available_at=_timestamp(row["available_at"]),
                value=float(row["value"]),
                source_ref=row["source_ref"],
            )
        )
    return tuple(result)


def _write_observation_file(path: Path, *, schema_version: str, validation_case: str, start: date, end_exclusive: date, observations: tuple[SeriesObservation, ...]) -> None:
    rows = [
        {
            "role": item.role.value,
            "measure": item.measure.value,
            "analysis_date": item.analysis_date.isoformat(),
            "observed_at": item.observed_at.isoformat().replace("+00:00", "Z"),
            "available_at": item.available_at.isoformat().replace("+00:00", "Z"),
            "value": item.value,
            "source_ref": item.source_ref,
        }
        for item in observations
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "validation_case": validation_case,
                "start": start.isoformat(),
                "end_exclusive": end_exclusive.isoformat(),
                "observation_count": len(rows),
                "observations": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


if __name__ == "__main__":
    main()
