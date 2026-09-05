import json
from pathlib import Path

import pytest

from orderscope_local.sec import (
    SecFormRejectionReason,
    classify_sec_form,
)


_FIXTURE_PATH = (
    Path(__file__).parents[1] / "fixtures" / "sec_form_filter_cases.json"
)
with _FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
    _CASES = json.load(fixture_file)


@pytest.mark.parametrize("case", _CASES["accepted"], ids=lambda case: case["raw_form"])
def test_accepts_reviewed_form_types(case: dict[str, object]) -> None:
    decision = classify_sec_form(str(case["raw_form"]))

    assert decision.accepted
    assert decision.raw_form == case["raw_form"]
    assert decision.family == case["family"]
    assert decision.is_amendment is case["is_amendment"]
    assert decision.rejection_reason is None


@pytest.mark.parametrize("raw_form", _CASES["rejected"])
def test_rejects_near_miss_and_unknown_forms_without_coercion(raw_form: str) -> None:
    decision = classify_sec_form(raw_form)

    assert not decision.accepted
    assert decision.raw_form == raw_form
    assert decision.family is None
    assert decision.is_amendment is None
    assert decision.rejection_reason is SecFormRejectionReason.UNSUPPORTED_FORM_TYPE


def test_fixture_covers_the_complete_reviewed_v01_allowlist() -> None:
    assert len(_CASES["accepted"]) == 28
    assert {case["raw_form"] for case in _CASES["accepted"]} == {
        "8-K",
        "8-K/A",
        "10-Q",
        "10-Q/A",
        "10-K",
        "10-K/A",
        "S-1",
        "S-1/A",
        "S-3",
        "S-3/A",
        "424B1",
        "424B2",
        "424B3",
        "424B4",
        "424B5",
        "424B7",
        "424B8",
        "DEF 14A",
        "SC 13D",
        "SC 13D/A",
        "SC 13G",
        "SC 13G/A",
        "SCHEDULE 13D",
        "SCHEDULE 13D/A",
        "SCHEDULE 13G",
        "SCHEDULE 13G/A",
        "4",
        "4/A",
    }


@pytest.mark.parametrize(
    ("legacy_raw_form", "current_raw_form", "family", "is_amendment"),
    [
        ("SC 13D", "SCHEDULE 13D", "13D", False),
        ("SC 13D/A", "SCHEDULE 13D/A", "13D", True),
        ("SC 13G", "SCHEDULE 13G", "13G", False),
        ("SC 13G/A", "SCHEDULE 13G/A", "13G", True),
    ],
)
def test_maps_legacy_and_current_schedule_names_to_the_same_family(
    legacy_raw_form: str,
    current_raw_form: str,
    family: str,
    is_amendment: bool,
) -> None:
    legacy = classify_sec_form(legacy_raw_form)
    current = classify_sec_form(current_raw_form)

    assert legacy.raw_form == legacy_raw_form
    assert current.raw_form == current_raw_form
    assert legacy.family == current.family == family
    assert legacy.is_amendment is current.is_amendment is is_amendment


def test_replay_preserves_base_amendment_and_duplicate_filing_identity() -> None:
    classified = [
        (
            filing["accession_number"],
            classify_sec_form(filing["raw_form"]),
        )
        for filing in _CASES["filing_replay"]
    ]

    assert classified[0][0] != classified[1][0]
    assert classified[0][1].family == classified[1][1].family == "10-K"
    assert classified[0][1].is_amendment is False
    assert classified[1][1].is_amendment is True
    assert classified[1] == classified[2]
