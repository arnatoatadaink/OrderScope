"""UWBS-021 catalyst repricing vocabulary."""
from enum import StrEnum


class CatalystDirection(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class ReactionDirection(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"


class CatalystRepricingInterpretationType(StrEnum):
    CATALYST_PRICE_DIVERGENCE = "catalyst_price_divergence"
    DELAYED_REPRICING = "delayed_repricing"


def reaction_supports_catalyst(catalyst: CatalystDirection, reaction: ReactionDirection) -> bool:
    return (catalyst is CatalystDirection.POSITIVE and reaction is ReactionDirection.POSITIVE) or (
        catalyst is CatalystDirection.NEGATIVE and reaction is ReactionDirection.NEGATIVE
    )


def reaction_contradicts_catalyst(catalyst: CatalystDirection, reaction: ReactionDirection) -> bool:
    return (catalyst is CatalystDirection.POSITIVE and reaction is ReactionDirection.NEGATIVE) or (
        catalyst is CatalystDirection.NEGATIVE and reaction is ReactionDirection.POSITIVE
    )
