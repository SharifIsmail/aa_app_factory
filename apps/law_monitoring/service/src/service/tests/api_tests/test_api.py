import os
from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from service.models import HealthResponse

from .conftest import SpyKernel


def test_get_health(
    test_client: TestClient,
) -> None:
    response = test_client.get("health")

    assert response.status_code == HTTPStatus.OK
    assert HealthResponse.model_validate_json(response.content) == HealthResponse(
        status="ok"
    )


@pytest.mark.skipif(
    os.getenv("GITHUB_REPOSITORY") is not None,
    reason="Makes multiple requests to the Pharia AI Inference API which does not work from Github at the moment. Test can only be executed locally in VPN.",
)
def test_quote_route(
    client_and_spy: tuple[TestClient, SpyKernel],
) -> None:
    client, spy = client_and_spy
    headers = {"Authorization": "Bearer token"}

    response = client.post("quote", json={}, headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"quote": "A real quote."}
