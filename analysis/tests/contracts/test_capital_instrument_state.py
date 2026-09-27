from orderscope_local.contracts.capital_instrument_state import CapitalInstrumentState, is_allowed_capital_instrument_transition


def test_capital_instrument_transitions() -> None:
    assert is_allowed_capital_instrument_transition(CapitalInstrumentState.ISSUED, CapitalInstrumentState.ACTIVE)
    assert is_allowed_capital_instrument_transition(CapitalInstrumentState.ACTIVE, CapitalInstrumentState.FULLY_REPAID)
    assert not is_allowed_capital_instrument_transition(CapitalInstrumentState.FULLY_REPAID, CapitalInstrumentState.ACTIVE)
