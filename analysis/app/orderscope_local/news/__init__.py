"""Provider-neutral News acquisition helpers for the local Corporate Canary."""

from .alpaca import (
    ALPACA_NEWS_PROVIDER_KEY,
    AlpacaNewsAdapter,
    AlpacaNewsRequestFailure,
    AlpacaNewsTransport,
    NewsArticleMetadata,
    decode_alpaca_news_timestamp,
)
from .body import (
    AlpacaNewsBodyAccessor,
    NewsBodyAcquisition,
    NewsBodyTransport,
    TemporaryBodyStore,
    exception_record,
)
from .duplicate import (
    NewsArticleComparison,
    NewsArticleComparisonKind,
    canonicalize_news_url,
    compare_news_articles,
)

__all__ = [
    "ALPACA_NEWS_PROVIDER_KEY",
    "AlpacaNewsAdapter",
    "AlpacaNewsBodyAccessor",
    "AlpacaNewsRequestFailure",
    "AlpacaNewsTransport",
    "NewsArticleComparison",
    "NewsArticleComparisonKind",
    "NewsArticleMetadata",
    "NewsBodyAcquisition",
    "NewsBodyTransport",
    "TemporaryBodyStore",
    "canonicalize_news_url",
    "compare_news_articles",
    "decode_alpaca_news_timestamp",
    "exception_record",
]
