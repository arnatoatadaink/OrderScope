from fastapi.testclient import TestClient
import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.local_api import (
    LOCALHOST_BIND_HOST,
    LOCAL_HEALTH_SCHEMA_VERSION,
    LocalServerBinding,
    create_health_app,
)


def test_default_binding_is_exact_ipv4_loopback() -> None:
    binding = LocalServerBinding()
    assert binding.host == "127.0.0.1"
    assert binding.host == LOCALHOST_BIND_HOST


@pytest.mark.parametrize(
    "host",
    (
        "0.0.0.0",
        "localhost",
        "::1",
        "::",
        "192.168.1.10",
        "10.0.0.2",
    ),
)
def test_external_or_alias_bind_hosts_are_rejected(host: str) -> None:
    with pytest.raises(ContractViolation, match="bind exactly to 127.0.0.1"):
        LocalServerBinding(host=host)


def test_health_endpoint_returns_only_bounded_local_metadata() -> None:
    app = create_health_app(binding=LocalServerBinding())
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "schema_version": LOCAL_HEALTH_SCHEMA_VERSION,
        "bind_host": "127.0.0.1",
    }


def test_health_app_retains_validated_binding_for_server_entrypoint() -> None:
    binding = LocalServerBinding()
    app = create_health_app(binding=binding)
    assert app.state.local_binding is binding


def test_unknown_routes_are_not_exposed_by_health_surface() -> None:
    client = TestClient(create_health_app())
    assert client.get("/facts").status_code == 404
    assert client.post("/health").status_code == 405


def test_binding_argument_must_use_validated_contract() -> None:
    with pytest.raises(ContractViolation, match="binding must be"):
        create_health_app(binding="127.0.0.1")  # type: ignore[arg-type]
