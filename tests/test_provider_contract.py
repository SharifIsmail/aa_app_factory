from __future__ import annotations

import inspect
from datetime import datetime
from typing import Protocol
from collections.abc import Iterable

import pytest

try:
    from service.models import LegalAct
except ModuleNotFoundError:  # pragma: no cover
    LegalAct = None  # type: ignore


class ProviderProtocol(Protocol):
    SOURCE_ID: str

    def fetch_legal_acts(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
    ) -> Iterable[LegalAct]:
        ...


@pytest.mark.skipif(LegalAct is None, reason="service.models not importable in this environment")
def test_provider_module_exposes_expected_api():
    module = pytest.importorskip(
        "external_sources.my_provider",
        reason="Provider module not implemented; import to run contract test",
    )

    assert hasattr(module, "SOURCE_ID"), "Provider must define SOURCE_ID constant"
    source_id = getattr(module, "SOURCE_ID")
    assert isinstance(source_id, str) and source_id, "SOURCE_ID must be a non-empty string"

    assert hasattr(module, "fetch_legal_acts"), "Provider must expose fetch_legal_acts"
    func = getattr(module, "fetch_legal_acts")
    assert callable(func), "fetch_legal_acts must be callable"

    signature = inspect.signature(func)
    expected_params = ["start_date", "end_date", "limit"]
    assert list(signature.parameters)[:3] == expected_params, (
        "fetch_legal_acts must accept (start_date, end_date, limit) parameters in order"
    )

    limit_param = signature.parameters["limit"]
    assert limit_param.default != inspect._empty, "limit parameter must have a default value"


@pytest.mark.skipif(LegalAct is None, reason="service.models not importable in this environment")
def test_provider_protocol_conformance():
    module = pytest.importorskip(
        "external_sources.my_provider",
        reason="Provider module not implemented; import to run protocol conformance test",
    )

    result = module.fetch_legal_acts(datetime.utcnow(), datetime.utcnow(), 1)
    assert isinstance(result, Iterable), "fetch_legal_acts must return an iterable of LegalAct"

    acts = list(result)
    if acts:  # Provider may legitimately return an empty list
        assert all(isinstance(act, LegalAct) for act in acts), (
            "Each item returned by fetch_legal_acts must be an instance of service.models.LegalAct"
        )
