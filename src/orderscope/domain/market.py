from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BarCadence(StrEnum):
    MINUTE_1 = "1m"
    MINUTE_15 = "15m"
    DAY_1 = "1d"


class MarketSession(StrEnum):
    PREMARKET = "premarket"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class NormalizedBar(BaseModel):
    """Provider-independent OHLCV contract used by OrderScope core."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1)
    timestamp_utc: datetime
    cadence: BarCadence
    session: MarketSession
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(ge=0)
    provider: str = Field(min_length=1)

    @field_validator("timestamp_utc")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("timestamp_utc must be normalized to UTC")
        return value

    @field_validator("high")
    @classmethod
    def validate_high(cls, value: float, info):
        values = info.data
        open_ = values.get("open")
        if open_ is not None and value < open_:
            raise ValueError("high must be >= open")
        return value

    @field_validator("close")
    @classmethod
    def validate_ohlc_range(cls, value: float, info):
        values = info.data
        low = values.get("low")
        high = values.get("high")
        if low is not None and value < low:
            raise ValueError("close must be >= low")
        if high is not None and value > high:
            raise ValueError("close must be <= high")
        return value
