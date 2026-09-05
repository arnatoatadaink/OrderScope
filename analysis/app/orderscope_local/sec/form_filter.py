"""Strict v0.1 classification for raw EDGAR form types.

The raw value is deliberately not trimmed, case-folded, or matched by prefix.
EDGAR form types outside the reviewed allowlist remain observable rejections so
that a future scope expansion is an explicit contract change.
"""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final


class SecFormFamily(StrEnum):
    CURRENT_REPORT = "8-K"
    QUARTERLY_REPORT = "10-Q"
    ANNUAL_REPORT = "10-K"
    REGISTRATION_S1 = "S-1"
    REGISTRATION_S3 = "S-3"
    PROSPECTUS_424B = "424B"
    DEFINITIVE_PROXY = "DEF 14A"
    BENEFICIAL_OWNERSHIP_13D = "13D"
    BENEFICIAL_OWNERSHIP_13G = "13G"
    INSIDER_OWNERSHIP_CHANGE = "4"


class SecFormRejectionReason(StrEnum):
    UNSUPPORTED_FORM_TYPE = "unsupported_form_type"


@dataclass(frozen=True, slots=True)
class _AcceptedForm:
    family: SecFormFamily
    is_amendment: bool


@dataclass(frozen=True, slots=True)
class SecFormDecision:
    """A classification decision that always preserves the exact input value."""

    raw_form: str
    family: SecFormFamily | None
    is_amendment: bool | None
    rejection_reason: SecFormRejectionReason | None

    @property
    def accepted(self) -> bool:
        return self.rejection_reason is None


_ACCEPTED_FORMS: Final = MappingProxyType(
    {
        "8-K": _AcceptedForm(SecFormFamily.CURRENT_REPORT, False),
        "8-K/A": _AcceptedForm(SecFormFamily.CURRENT_REPORT, True),
        "10-Q": _AcceptedForm(SecFormFamily.QUARTERLY_REPORT, False),
        "10-Q/A": _AcceptedForm(SecFormFamily.QUARTERLY_REPORT, True),
        "10-K": _AcceptedForm(SecFormFamily.ANNUAL_REPORT, False),
        "10-K/A": _AcceptedForm(SecFormFamily.ANNUAL_REPORT, True),
        "S-1": _AcceptedForm(SecFormFamily.REGISTRATION_S1, False),
        "S-1/A": _AcceptedForm(SecFormFamily.REGISTRATION_S1, True),
        "S-3": _AcceptedForm(SecFormFamily.REGISTRATION_S3, False),
        "S-3/A": _AcceptedForm(SecFormFamily.REGISTRATION_S3, True),
        "424B1": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "424B2": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "424B3": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "424B4": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "424B5": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "424B7": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "424B8": _AcceptedForm(SecFormFamily.PROSPECTUS_424B, False),
        "DEF 14A": _AcceptedForm(SecFormFamily.DEFINITIVE_PROXY, False),
        # EDGAR historical filings use SC 13D/G while current structured
        # filings use SCHEDULE 13D/G. Preserve either exact raw value and map
        # both spellings to the same provider-neutral family.
        "SC 13D": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13D, False
        ),
        "SC 13D/A": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13D, True
        ),
        "SC 13G": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13G, False
        ),
        "SC 13G/A": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13G, True
        ),
        "SCHEDULE 13D": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13D, False
        ),
        "SCHEDULE 13D/A": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13D, True
        ),
        "SCHEDULE 13G": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13G, False
        ),
        "SCHEDULE 13G/A": _AcceptedForm(
            SecFormFamily.BENEFICIAL_OWNERSHIP_13G, True
        ),
        "4": _AcceptedForm(SecFormFamily.INSIDER_OWNERSHIP_CHANGE, False),
        "4/A": _AcceptedForm(SecFormFamily.INSIDER_OWNERSHIP_CHANGE, True),
    }
)


def classify_sec_form(raw_form: str) -> SecFormDecision:
    """Classify one exact EDGAR form type without provider-specific coercion."""

    accepted_form = _ACCEPTED_FORMS.get(raw_form)
    if accepted_form is None:
        return SecFormDecision(
            raw_form=raw_form,
            family=None,
            is_amendment=None,
            rejection_reason=SecFormRejectionReason.UNSUPPORTED_FORM_TYPE,
        )

    return SecFormDecision(
        raw_form=raw_form,
        family=accepted_form.family,
        is_amendment=accepted_form.is_amendment,
        rejection_reason=None,
    )
