from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.catalyst_reaction_window import CatalystReactionObservation, CatalystReactionWindow

UTC = timezone.utc


def _obs(**overrides: object) -> CatalystReactionObservation:
    values: dict[str, object] = {
        "subject_ref": "instrument:TNON",
        "catalyst_ref": "fact:capital-structure:tnon",
        "window": CatalystReactionWindow.REACTION_SESSION_CLOSE,
        "window_start": datetime(2026, 9, 9, 13, 30, tzinfo=UTC),
        "window_end": datetime(2026, 9, 9, 20, 0, tzinfo=UTC),
        "return_percent": -27.38,
        "volume_ratio": 10.0,
        "realized_volatility_ratio": 4.0,
        "source_record_ids": ("fact:market:tnon:open", "fact:market:tnon:close"),
        "calculated_at": datetime(2026, 9, 9, 20, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return CatalystReactionObservation(**values)


def test_negative_return_is_valid_observation() -> None:
    assert _obs().return_percent == -27.38


def test_requires_lineage_and_nonnegative_ratios() -> None:
    with pytest.raises(ContractViolation, match="source_record_ids"):
        _obs(source_record_ids=())
    with pytest.raises(ContractViolation, match="volume_ratio"):
        _obs(volume_ratio=-0.1)


def test_calculation_cannot_precede_window_end() -> None:
    with pytest.raises(ContractViolation, match="calculated_at"):
        _obs(calculated_at=datetime(2026, 9, 9, 19, 59, tzinfo=UTC))
