from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from orderscope.domain.market import BarCadence


class UniverseTier(BaseModel):
    model_config = ConfigDict(frozen=True)

    cadence: BarCadence
    groups: dict[str, list[str]]

    @property
    def symbols(self) -> list[str]:
        return [symbol for symbols in self.groups.values() for symbol in symbols]


class UniverseConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str
    source_of_truth: str
    policy: dict[str, object]
    tiers: dict[str, UniverseTier]

    @property
    def symbols(self) -> list[str]:
        return [symbol for tier in self.tiers.values() for symbol in tier.symbols]

    def symbols_for_cadence(self, cadence: BarCadence) -> list[str]:
        return [
            symbol
            for tier in self.tiers.values()
            if tier.cadence == cadence
            for symbol in tier.symbols
        ]


def load_universe(path: str | Path) -> UniverseConfig:
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    config = UniverseConfig.model_validate(payload)

    symbols = config.symbols
    if len(symbols) != len(set(symbols)):
        duplicates = sorted({symbol for symbol in symbols if symbols.count(symbol) > 1})
        raise ValueError(f"duplicate universe symbols: {duplicates}")

    if not symbols:
        raise ValueError("universe must not be empty")

    return config
