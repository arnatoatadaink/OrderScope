from __future__ import annotations

from dataclasses import asdict
from datetime import date
import json
import os
from pathlib import Path

from orderscope_local.cross_market import (
    AlpacaDailyBarsTransport,
    DEFAULT_A0_ALPACA_BINDINGS,
    collect_a0_alpaca_daily,
    load_source_manifest,
)
from orderscope_local.cross_market.validation import SeriesMeasure


MANIFEST = Path("analysis/config/cross_market/a0-002-sources-v0.1.json")
OUTPUT = Path("var/cross-market/a0-002/alpaca-daily-observations.json")


def main() -> None:
    manifest = load_source_manifest(MANIFEST)
    expected = {
        (spec.role, spec.measure): spec.source_ref
        for spec in manifest.series
        if spec.source_ref.startswith("alpaca:")
    }
    for binding in DEFAULT_A0_ALPACA_BINDINGS:
        price_ref = expected.get((binding.role, SeriesMeasure.PRICE))
        if price_ref != binding.source_ref:
            raise RuntimeError(f"A0-002 Alpaca source manifest drift for {binding.role.value}:PRICE")
        if not binding.is_crypto:
            volume_ref = expected.get((binding.role, SeriesMeasure.VOLUME))
            if volume_ref != binding.source_ref:
                raise RuntimeError(f"A0-002 Alpaca source manifest drift for {binding.role.value}:VOLUME")

    transport = AlpacaDailyBarsTransport(environ=os.environ)
    start = manifest.windows.baseline_start.date()
    end_exclusive = manifest.windows.primary_end.date()
    observations = collect_a0_alpaca_daily(
        transport=transport,
        start=start,
        end_exclusive=end_exclusive,
    )

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
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "a0-002-alpaca-observations-v0.1",
                "validation_case": manifest.validation_case,
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
    print(f"output            = {OUTPUT}")
    print(f"observation_count = {len(rows)}")
    print("A0-002 Alpaca daily collection = PASS")


if __name__ == "__main__":
    main()
