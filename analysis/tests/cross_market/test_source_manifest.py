from __future__ import annotations

from pathlib import Path

from orderscope_local.cross_market import SeriesMeasure, SeriesRole, load_source_manifest


MANIFEST = Path("analysis/config/cross_market/a0-002-sources-v0.1.json")


def test_loads_reviewed_a0_002_source_manifest() -> None:
    manifest = load_source_manifest(MANIFEST)
    assert manifest.validation_case == "CBRS_2026-09-01_2026-09-04"
    assert len(manifest.series) == 12
    keys = {(item.role, item.measure) for item in manifest.series}
    assert (SeriesRole.CBRS, SeriesMeasure.PRICE) in keys
    assert (SeriesRole.CBRS, SeriesMeasure.VOLUME) in keys
    assert (SeriesRole.JGB_10Y, SeriesMeasure.YIELD) in keys
    assert (SeriesRole.USDJPY, SeriesMeasure.FX_RATE) in keys
    assert set(manifest.unresolved_optional) == {
        (SeriesRole.CBRS, SeriesMeasure.CONSENSUS_TARGET),
        (SeriesRole.CBRS, SeriesMeasure.SHORT_METRIC),
    }


def test_manifest_uses_reviewed_v0_1_proxy_choices() -> None:
    manifest = load_source_manifest(MANIFEST)
    by_key = {(item.role, item.measure): item for item in manifest.series}
    assert by_key[(SeriesRole.US_MARKET, SeriesMeasure.PRICE)].series_id == "QQQ.close"
    assert by_key[(SeriesRole.AI_SEMICONDUCTOR_PROXY, SeriesMeasure.PRICE)].series_id == "SOXX.close"
    assert by_key[(SeriesRole.UST_10Y, SeriesMeasure.YIELD)].series_id == "DGS10"
    assert by_key[(SeriesRole.JGB_10Y, SeriesMeasure.YIELD)].series_id == "MOF.JGB.CONSTANT_MATURITY.10Y"
    assert by_key[(SeriesRole.USDJPY, SeriesMeasure.FX_RATE)].series_id == "BOJ.USDJPY.17H"
