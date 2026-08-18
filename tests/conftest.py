"""Fixtures and doubles shared by the test suite.

No test touches a real database or a real network: the doubles below stand in
for the ClickHouse client, the MariaDB driver and the HTTP layer, so the suite
runs anywhere with no service to start.
"""

from collections.abc import Iterator

import pytest

from ingestion_engine import Column, TableConfig


@pytest.fixture
def table() -> TableConfig:
    """A minimal valid table, with one flat column and one nested one."""

    return TableConfig(
        name="events",
        columns=[
            Column("id", "UInt64", "id"),
            Column("label", "String", "meta.label"),
        ],
        order_by="id",
        source="test",
    )


class FakeClickHouseClient:
    """Records what the loader asks ClickHouse to do."""

    def __init__(self, number: int, insert_error: Exception | None = None):
        self.number = number
        self.insert_error = insert_error
        self.commands: list[str] = []
        self.inserts: list[tuple[str, list[tuple]]] = []
        self.closed = False

    def command(self, sql: str) -> None:
        self.commands.append(sql)

    def insert(self, table: str | None = None, data=None) -> None:
        if self.insert_error is not None:
            raise self.insert_error

        self.inserts.append((table, list(data)))

    def close(self) -> None:
        self.closed = True


class ClientFactory:
    """Stands in for clickhouse_connect.get_client and tracks what it created.

    Args:
        insert_errors: One entry per client to be created. A non None entry
            makes that client fail on insert, which is how a dropped
            connection is simulated.
    """

    def __init__(self, insert_errors: list[Exception | None] | None = None):
        self.clients: list[FakeClickHouseClient] = []
        self._insert_errors = list(insert_errors or [])
        self.kwargs: list[dict] = []

    def __call__(self, **kwargs) -> FakeClickHouseClient:
        self.kwargs.append(kwargs)

        error = self._insert_errors.pop(0) if self._insert_errors else None
        client = FakeClickHouseClient(len(self.clients) + 1, error)
        self.clients.append(client)

        return client

    @property
    def opened(self) -> int:
        """Number of connections opened so far."""

        return len(self.clients)

    @property
    def closed(self) -> int:
        """Number of connections closed so far."""

        return sum(1 for client in self.clients if client.closed)


@pytest.fixture
def patch_client_factory(monkeypatch: pytest.MonkeyPatch):
    """Install a double in place of the ClickHouse client factory.

    Returns:
        A callable taking the optional per-client insert errors and returning
        the installed ClientFactory.
    """

    def install(insert_errors: list[Exception | None] | None = None) -> ClientFactory:
        factory = ClientFactory(insert_errors)
        monkeypatch.setattr("clickhouse_connect.get_client", factory)

        return factory

    return install


@pytest.fixture
def client_factory(patch_client_factory) -> ClientFactory:
    """A ClickHouse client factory double whose clients always succeed."""

    return patch_client_factory()


class CountingSource:
    """An iterable that reports how many records have been pulled from it.

    Used to prove that extraction and normalization stay lazy.
    """

    def __init__(self, records: list[dict]):
        self.records = records
        self.consumed = 0

    def __iter__(self) -> Iterator[dict]:
        for record in self.records:
            self.consumed += 1
            yield record


@pytest.fixture
def counting_source() -> type[CountingSource]:
    """Factory building an iterable that counts how much of it was consumed."""

    return CountingSource
