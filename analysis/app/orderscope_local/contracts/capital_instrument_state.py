"""Capital-instrument lifecycle vocabulary for UWBS-017."""

from __future__ import annotations

from enum import StrEnum

from .errors import ContractViolation


class CapitalInstrumentKind(StrEnum):
    SENIOR_CONVERTIBLE_NOTE = "senior_convertible_note"
    CONVERTIBLE_NOTE = "convertible_note"
    PROMISSORY_NOTE = "promissory_note"
    WARRANT = "warrant"
    PREFERRED_STOCK = "preferred_stock"


class CapitalInstrumentState(StrEnum):
    ISSUED = "issued"
    ACTIVE = "active"
    CONVERSION_WINDOW_OPEN = "conversion_window_open"
    PARTIALLY_REPAID = "partially_repaid"
    FULLY_REPAID = "fully_repaid"
    EXTENDED = "extended"
    REFINANCED = "refinanced"
    CONVERTED = "converted"
    TERMINATED = "terminated"


_ALLOWED_TRANSITIONS: dict[CapitalInstrumentState, frozenset[CapitalInstrumentState]] = {
    CapitalInstrumentState.ISSUED: frozenset({CapitalInstrumentState.ACTIVE, CapitalInstrumentState.TERMINATED}),
    CapitalInstrumentState.ACTIVE: frozenset({
        CapitalInstrumentState.CONVERSION_WINDOW_OPEN,
        CapitalInstrumentState.PARTIALLY_REPAID,
        CapitalInstrumentState.FULLY_REPAID,
        CapitalInstrumentState.EXTENDED,
        CapitalInstrumentState.REFINANCED,
        CapitalInstrumentState.CONVERTED,
        CapitalInstrumentState.TERMINATED,
    }),
    CapitalInstrumentState.CONVERSION_WINDOW_OPEN: frozenset({
        CapitalInstrumentState.PARTIALLY_REPAID,
        CapitalInstrumentState.FULLY_REPAID,
        CapitalInstrumentState.EXTENDED,
        CapitalInstrumentState.REFINANCED,
        CapitalInstrumentState.CONVERTED,
        CapitalInstrumentState.TERMINATED,
    }),
    CapitalInstrumentState.PARTIALLY_REPAID: frozenset({
        CapitalInstrumentState.FULLY_REPAID,
        CapitalInstrumentState.EXTENDED,
        CapitalInstrumentState.REFINANCED,
        CapitalInstrumentState.CONVERTED,
        CapitalInstrumentState.TERMINATED,
    }),
    CapitalInstrumentState.EXTENDED: frozenset({
        CapitalInstrumentState.CONVERSION_WINDOW_OPEN,
        CapitalInstrumentState.PARTIALLY_REPAID,
        CapitalInstrumentState.FULLY_REPAID,
        CapitalInstrumentState.REFINANCED,
        CapitalInstrumentState.CONVERTED,
        CapitalInstrumentState.TERMINATED,
    }),
    CapitalInstrumentState.FULLY_REPAID: frozenset(),
    CapitalInstrumentState.REFINANCED: frozenset(),
    CapitalInstrumentState.CONVERTED: frozenset(),
    CapitalInstrumentState.TERMINATED: frozenset(),
}


def is_allowed_capital_instrument_transition(
    previous: CapitalInstrumentState,
    current: CapitalInstrumentState,
) -> bool:
    if not isinstance(previous, CapitalInstrumentState) or not isinstance(current, CapitalInstrumentState):
        raise ContractViolation("capital-instrument transition requires CapitalInstrumentState values")
    return current in _ALLOWED_TRANSITIONS[previous]
