"""Provider-neutral News acquisition and extraction helpers for the local Corporate Canary."""

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
from .event_taxonomy import (
    NEWS_EVENT_TAXONOMY_VERSION,
    EventTaxonomyEntry,
    NewsEventType,
    event_taxonomy_entry,
    news_event_taxonomy,
)

__all__ = [
    "ALPACA_NEWS_PROVIDER_KEY",
    "AlpacaNewsAdapter",
    "AlpacaNewsBodyAccessor",
    "AlpacaNewsRequestFailure",
    "AlpacaNewsTransport",
    "EventTaxonomyEntry",
    "NEWS_EVENT_TAXONOMY_VERSION",
    "NewsArticleComparison",
    "NewsArticleComparisonKind",
    "NewsArticleMetadata",
    "NewsBodyAcquisition",
    "NewsBodyTransport",
    "NewsEventType",
    "TemporaryBodyStore",
    "canonicalize_news_url",
    "compare_news_articles",
    "decode_alpaca_news_timestamp",
    "event_taxonomy_entry",
    "exception_record",
    "news_event_taxonomy",
]
