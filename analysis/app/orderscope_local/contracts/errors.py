"""Shared contract errors with no dependency on a specific contract module."""


class ContractViolation(ValueError):
    """Raised when data crosses a provider-neutral boundary incorrectly."""
