from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from service.law_core.background_work.reconciliation_worker import (
    ReconciliationWorker,
)
from service.models import DocumentTypeLabel, LegalAct, OfficialJournalSeries


class DummyStorage:
    def __init__(self) -> None:
        self.files: dict[tuple[str, str], str] = {}

    def file_exists(self, folder: str, name: str) -> bool:
        return (folder, name) in self.files

    def load_file(self, folder: str, name: str) -> Optional[str]:
        return self.files.get((folder, name))

    def save_file(self, folder: str, name: str, content: str) -> None:
        self.files[(folder, name)] = content


def _legal_act_with_labels(expression_url: str) -> LegalAct:
    now = datetime.utcnow()
    return LegalAct(
        expression_url=expression_url,
        title="Test Act",
        pdf_url="http://example.com/doc.pdf",
        eurovoc_labels=["environment", "food"],
        document_date=now,
        publication_date=now,
        effect_date=None,
        end_validity_date=None,
        notification_date=None,
        document_type="http://example.com/doc-type",
        document_type_label=DocumentTypeLabel.DIRECTIVE,
        oj_series_label=OfficialJournalSeries.L_SERIES,
    )


def _db_law(
    law_id: str, expression_url: str, eurovoc_labels: Optional[list[str]]
) -> Any:
    now = datetime.utcnow() - timedelta(days=1)
    return SimpleNamespace(
        law_id=law_id,
        expression_url=expression_url,
        eurovoc_labels=eurovoc_labels,
        pdf_url="",
        document_type_label=None,
        document_type=None,
        oj_series_label=None,
        document_date=None,
        effect_date=None,
        end_validity_date=None,
        notification_date=None,
    )


@pytest.fixture()
def worker(monkeypatch: pytest.MonkeyPatch) -> ReconciliationWorker:
    w = ReconciliationWorker()

    # Inject dummy storage to avoid IO
    dummy_storage = DummyStorage()
    monkeypatch.setattr(w, "storage_backend", dummy_storage, raising=True)

    # Avoid accessing real DB in constructor-created DAO by replacing DAO later per test
    return w


def test_eurovoc_backfill_success(
    monkeypatch: pytest.MonkeyPatch, worker: ReconciliationWorker
) -> None:
    # Arrange: DAO returns 2 laws, one missing labels and one already having labels
    law_missing = _db_law("law_1", "http://exp/1", eurovoc_labels=[])
    law_has = _db_law("law_2", "http://exp/2", eurovoc_labels=["energy"])

    dao_calls: dict[str, Any] = {"updates": []}

    class FakeDAO:
        def list_by_date_range(self, start_date=None, end_date=None, limit: int = 1000):  # type: ignore[no-untyped-def]
            return [law_missing, law_has]

        def update_law_fields(self, law_id: str, update_fields: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
            dao_calls["updates"].append((law_id, update_fields))

    monkeypatch.setattr(worker, "laws_dao", FakeDAO(), raising=True)

    # Mock EUR-Lex service methods used earlier in _do_work so we don't hit network
    class FakeActsResponse:
        def __init__(self) -> None:
            self.legal_acts: list[LegalAct] = []

    class FakeEurLex:
        def get_legal_acts_by_date_range(self, start, end):  # type: ignore[no-untyped-def]
            return FakeActsResponse()

        def get_legal_act_by_expression_url(
            self, expression_url: str
        ) -> Optional[LegalAct]:  # type: ignore[no-untyped-def]
            return _legal_act_with_labels(expression_url)

    # Monkeypatch the imported singleton reference used inside the module
    monkeypatch.setattr(
        "service.law_core.background_work.reconciliation_worker.eur_lex_service",
        FakeEurLex(),
        raising=True,
    )

    # Act
    result = worker._do_work()

    # Assert
    assert result["status"] == "completed"
    assert result.get("eurovoc_backfill_error") is None
    # 2 checked (one missing, one has labels), only the missing one updated
    assert result["eurovoc_backfill_checked"] == 2
    assert result["eurovoc_backfill_updated"] == 1
    # Verify DAO update was called exactly once with eurovoc_labels
    assert len(dao_calls["updates"]) == 1
    law_id, update_fields = dao_calls["updates"][0]
    assert law_id == "law_1"
    assert (
        "eurovoc_labels" in update_fields and len(update_fields["eurovoc_labels"]) > 0
    )


def test_eurovoc_backfill_handles_refresh_failure(
    monkeypatch: pytest.MonkeyPatch, worker: ReconciliationWorker
) -> None:
    # Arrange: one law missing labels, but refresh raises
    law_missing = _db_law("law_3", "http://exp/3", eurovoc_labels=None)

    class FakeDAO:
        def list_by_date_range(self, start_date=None, end_date=None, limit: int = 1000):  # type: ignore[no-untyped-def]
            return [law_missing]

        def update_law_fields(self, law_id: str, update_fields: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
            raise AssertionError("Should not update on refresh failure")

    monkeypatch.setattr(worker, "laws_dao", FakeDAO(), raising=True)

    class FakeActsResponse:
        def __init__(self) -> None:
            self.legal_acts: list[LegalAct] = []

    class FakeEurLex:
        def get_legal_acts_by_date_range(self, start, end):  # type: ignore[no-untyped-def]
            return FakeActsResponse()

        def get_legal_act_by_expression_url(
            self, expression_url: str
        ) -> Optional[LegalAct]:  # type: ignore[no-untyped-def]
            raise RuntimeError("network error")

    monkeypatch.setattr(
        "service.law_core.background_work.reconciliation_worker.eur_lex_service",
        FakeEurLex(),
        raising=True,
    )

    # Act
    result = worker._do_work()

    # Assert: still completes, counts 1 checked, 0 updated, no global error since failures are handled per-law
    assert result["status"] == "completed"
    assert result.get("eurovoc_backfill_error") is None
    assert result["eurovoc_backfill_checked"] == 1
    assert result["eurovoc_backfill_updated"] == 0
