"""Non-secret local configuration and credential-name boundary for OrderScope."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from orderscope_local.contracts import ContractViolation


DATA_ROOT_ENV = "ORDERSCOPE_DATA_ROOT"
LOG_LEVEL_ENV = "ORDERSCOPE_LOG_LEVEL"
SEC_USER_AGENT_ENV = "ORDERSCOPE_SEC_USER_AGENT"
ALPACA_API_KEY_ENV = "ORDERSCOPE_SECRET_ALPACA_API_KEY"
ALPACA_API_SECRET_ENV = "ORDERSCOPE_SECRET_ALPACA_API_SECRET"
SECRET_ENV_PREFIX = "ORDERSCOPE_SECRET_"

DEFAULT_DATA_ROOT = Path("var")
DEFAULT_LOG_LEVEL = "INFO"
_ALLOWED_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})

SECRET_ENV_NAMES = frozenset({ALPACA_API_KEY_ENV, ALPACA_API_SECRET_ENV})
NON_SECRET_ENV_NAMES = frozenset({DATA_ROOT_ENV, LOG_LEVEL_ENV, SEC_USER_AGENT_ENV})


@dataclass(frozen=True, slots=True)
class LocalConfig:
    """Validated non-secret local configuration.

    Secret values are intentionally absent from this type. Provider credentials
    remain process-local environment values consumed only by the adapter that
    requires them.
    """

    data_root: Path = DEFAULT_DATA_ROOT
    log_level: str = DEFAULT_LOG_LEVEL
    sec_user_agent: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.data_root, Path):
            raise ContractViolation("data_root must be pathlib.Path")
        if not str(self.data_root).strip():
            raise ContractViolation("data_root must not be empty")
        if self.log_level not in _ALLOWED_LOG_LEVELS:
            raise ContractViolation("unsupported log level")
        if self.sec_user_agent is not None and not self.sec_user_agent.strip():
            raise ContractViolation("SEC user agent must be non-empty when configured")

    def log_fields(self) -> dict[str, str | None]:
        """Return a logging-safe projection containing no credential values."""

        return {
            "data_root": str(self.data_root),
            "log_level": self.log_level,
            "sec_user_agent": self.sec_user_agent,
        }


def load_local_config(environ: Mapping[str, str]) -> LocalConfig:
    """Load only the non-secret configuration surface from an environment mapping."""

    data_root_raw = environ.get(DATA_ROOT_ENV)
    data_root = Path(data_root_raw) if data_root_raw is not None else DEFAULT_DATA_ROOT

    log_level = environ.get(LOG_LEVEL_ENV, DEFAULT_LOG_LEVEL).upper()
    sec_user_agent = environ.get(SEC_USER_AGENT_ENV)

    return LocalConfig(
        data_root=data_root,
        log_level=log_level,
        sec_user_agent=sec_user_agent,
    )


def read_required_secret(environ: Mapping[str, str], name: str) -> str:
    """Read one explicitly registered secret without embedding it in config state."""

    if name not in SECRET_ENV_NAMES or not name.startswith(SECRET_ENV_PREFIX):
        raise ContractViolation("unregistered secret environment variable")
    value = environ.get(name)
    if value is None or not value:
        raise ContractViolation(f"required credential is not configured: {name}")
    return value


def redact_environment_for_logging(environ: Mapping[str, str]) -> dict[str, str]:
    """Return an environment projection with all OrderScope secret values redacted."""

    result: dict[str, str] = {}
    for name, value in environ.items():
        if name.startswith(SECRET_ENV_PREFIX):
            result[name] = "<redacted>"
        elif name in NON_SECRET_ENV_NAMES:
            result[name] = value
    return result
