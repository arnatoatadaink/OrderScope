"""Provider-neutral News acquisition helpers for the local Corporate Canary."""

from .alpaca import (
    ALPACA_NEWS_PROVIDER_KEY,
    AlpacaNewsAdapter,
    AlpacaNewsRequestFailure,
    AlpacaNewsTransport,
    NewsArticleMetadata,
    decode_alpaca_news_timestamp,
)

__all__ = [
    "ALPACA_NEWS_PROVIDER_KEY",
    "AlpacaNewsAdapter",
    "AlpacaNewsRequestFailure",
    "AlpacaNewsTransport",
    "NewsArticleMetadata",
    "decode_alpaca_news_timestamp",
]
