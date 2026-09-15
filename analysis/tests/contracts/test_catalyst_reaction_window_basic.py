from __future__ import annotations

from datetime import datetime, timezone

from orderscope_local.contracts.catalyst_reaction_window import CatalystReactionObservation, CatalystReactionWindow

UTC = timezone.utc


def test_reaction_window_materializes_without_price_rediscovery_classification() -> None:
    obs = CatalystReactionObservation(
        subject_ref="instrument:CHPT",
        catalyst_ref="fact:earnings:chpt-2026q2",
        window=CatalystReactionWindow.REACTION_NEXT_CLOSE,
        window_start=datetime(2026, 9, 3, 13, 30, tzinfo=UTC),
        window_end=datetime(2026, 9, 3, 20, 0, tzinfo=UTC),
        return_percent=74.95,
        volume_ratio=27.0,
        realized_volatility_ratio=5.0,
        source_record_ids=("fact:market:chpt:pre", "fact:market:chpt:post"),
        calculated_at=datetime(2026, 9, 3, 20, 1, tzinfo=UTC),
    )
    metric = obs.to_derived_metric(
        record_id="metric:chpt:reaction-next-close",
        accepted_at=datetime(2026, 9, 3, 20, 2, tzinfo=UTC),
    )
    assert metric.metric_name == "catalyst_reaction_window"
    assert metric.value["window"] == "reaction_next_close"
    assert metric.value["return_percent"] == 74.95
    assert "price_rediscovery" not in metric.value
