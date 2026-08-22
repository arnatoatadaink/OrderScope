from pathlib import Path

from orderscope.domain.market import BarCadence
from orderscope.universe import load_universe


UNIVERSE_PATH = Path("config/universe.v0.1.yaml")


def test_v01_universe_matches_fixed_source_count() -> None:
    universe = load_universe(UNIVERSE_PATH)

    assert len(universe.symbols) == 102
    assert len(set(universe.symbols)) == 102


def test_v01_cadence_partition() -> None:
    universe = load_universe(UNIVERSE_PATH)

    assert len(universe.symbols_for_cadence(BarCadence.MINUTE_1)) == 25
    assert len(universe.symbols_for_cadence(BarCadence.MINUTE_15)) == 24
    assert len(universe.symbols_for_cadence(BarCadence.DAY_1)) == 53


def test_v01_known_symbols_keep_source_cadence() -> None:
    universe = load_universe(UNIVERSE_PATH)

    assert "CBRS" in universe.symbols_for_cadence(BarCadence.MINUTE_1)
    assert "MARA" in universe.symbols_for_cadence(BarCadence.MINUTE_15)
    assert "EWJ" in universe.symbols_for_cadence(BarCadence.DAY_1)
