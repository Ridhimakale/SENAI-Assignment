from datetime import UTC, datetime

import pytest

import app.db.base
from app.models.contact import Contact
from app.models.thread import Thread
from app.repositories.ingestion import IngestionRepository


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self):
        self.queries = []
        self.added = []

    async def execute(self, query):
        self.queries.append(query)
        return FakeResult(None)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_thread_lookup_uses_thread_id_and_sender() -> None:
    session = FakeSession()
    repository = IngestionRepository(session)  # type: ignore[arg-type]
    contact = Contact(id=1, email="alice@example.com")

    thread = await repository.get_or_create_thread(
        external_thread_id="thread_shared",
        contact=contact,
        sender="alice@example.com",
        subject="Question",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )

    compiled_query = str(session.queries[0])
    assert "threads.thread_id" in compiled_query
    assert "threads.sender_email" in compiled_query
    assert isinstance(thread, Thread)
