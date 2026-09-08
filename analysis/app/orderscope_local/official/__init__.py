"""Official-source registry and downstream official-context helpers."""

from .registry import (
    OFFICIAL_ACTORS,
    OFFICIAL_SOURCES,
    ContentActorMode,
    OfficialActor,
    OfficialActorKind,
    OfficialSource,
    OfficialSourceLane,
    OfficialSourceType,
    get_official_actor,
    get_official_source,
    validate_official_registry,
)

__all__ = [
    "OFFICIAL_ACTORS",
    "OFFICIAL_SOURCES",
    "ContentActorMode",
    "OfficialActor",
    "OfficialActorKind",
    "OfficialSource",
    "OfficialSourceLane",
    "OfficialSourceType",
    "get_official_actor",
    "get_official_source",
    "validate_official_registry",
]
