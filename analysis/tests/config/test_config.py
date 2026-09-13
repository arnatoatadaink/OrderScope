from pathlib import Path

import pytest

from orderscope_local.config import (
    ALPACA_API_KEY_ENV,
    ALPACA_API_SECRET_ENV,
    DATA_ROOT_ENV,
    LOG_LEVEL_ENV,
    SEC_USER_AGENT_ENV,
    LocalConfig,
    load_local_config,
    read_required_secret,
    redact_environment_for_logging,
)
from orderscope_local.contracts import ContractViolation


def test_load_local_config_uses_safe_defaults() -> None:
    config = load_local_config({})

    assert config == LocalConfig(data_root=Path("var"), log_level="INFO", sec_user_agent=None)


def test_load_local_config_reads_only_non_secret_values() -> None:
    environment = {
        DATA_ROOT_ENV: "/home/test/orderscope-var",
        LOG_LEVEL_ENV: "debug",
        SEC_USER_AGENT_ENV: "OrderScope test@example.invalid",
        ALPACA_API_KEY_ENV: "key-secret-value",
        ALPACA_API_SECRET_ENV: "secret-secret-value",
    }

    config = load_local_config(environment)

    assert config.data_root == Path("/home/test/orderscope-var")
    assert config.log_level == "DEBUG"
    assert config.sec_user_agent == "OrderScope test@example.invalid"
    assert "key-secret-value" not in repr(config)
    assert "secret-secret-value" not in repr(config)


def test_invalid_log_level_fails_closed() -> None:
    with pytest.raises(ContractViolation, match="unsupported log level"):
        load_local_config({LOG_LEVEL_ENV: "verbose"})


def test_blank_sec_user_agent_fails_closed() -> None:
    with pytest.raises(ContractViolation, match="SEC user agent"):
        load_local_config({SEC_USER_AGENT_ENV: "   "})


def test_registered_secret_can_be_read_without_entering_config() -> None:
    environment = {ALPACA_API_KEY_ENV: "local-key"}

    assert read_required_secret(environment, ALPACA_API_KEY_ENV) == "local-key"
    assert load_local_config(environment) == LocalConfig()


def test_missing_secret_fails_without_echoing_secret_value() -> None:
    with pytest.raises(ContractViolation, match=ALPACA_API_SECRET_ENV):
        read_required_secret({}, ALPACA_API_SECRET_ENV)


def test_unregistered_secret_name_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="unregistered secret"):
        read_required_secret({"OTHER_SECRET": "value"}, "OTHER_SECRET")


def test_logging_projection_never_contains_secret_values() -> None:
    environment = {
        DATA_ROOT_ENV: "/srv/orderscope",
        LOG_LEVEL_ENV: "INFO",
        SEC_USER_AGENT_ENV: "OrderScope test@example.invalid",
        ALPACA_API_KEY_ENV: "top-secret-key",
        ALPACA_API_SECRET_ENV: "top-secret-secret",
        "ORDERSCOPE_SECRET_FUTURE_PROVIDER_TOKEN": "future-secret",
        "UNRELATED": "not-part-of-orderscope-config",
    }

    projection = redact_environment_for_logging(environment)
    rendered = repr(projection)

    assert projection[ALPACA_API_KEY_ENV] == "<redacted>"
    assert projection[ALPACA_API_SECRET_ENV] == "<redacted>"
    assert projection["ORDERSCOPE_SECRET_FUTURE_PROVIDER_TOKEN"] == "<redacted>"
    assert projection[DATA_ROOT_ENV] == "/srv/orderscope"
    assert "top-secret-key" not in rendered
    assert "top-secret-secret" not in rendered
    assert "future-secret" not in rendered
    assert "UNRELATED" not in projection


def test_log_fields_are_secret_free() -> None:
    config = LocalConfig(
        data_root=Path("/srv/orderscope"),
        log_level="WARNING",
        sec_user_agent="OrderScope test@example.invalid",
    )

    fields = config.log_fields()

    assert fields == {
        "data_root": "/srv/orderscope",
        "log_level": "WARNING",
        "sec_user_agent": "OrderScope test@example.invalid",
    }
