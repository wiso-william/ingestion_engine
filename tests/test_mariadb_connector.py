"""Tests for MariaDBConnector, driven through a fake driver.

The driver is replaced in sys.modules rather than on the connector, so
load_driver() runs for real and these tests need neither a server nor the
MariaDB Connector/C the driver builds against.
"""

import subprocess
import sys
from typing import Any

import pytest

from ingestion_engine import MariaDBConfig, MariaDBConnector


class FakeError(Exception):
    """Stands in for mariadb.Error."""


class FakeCursor:
    def __init__(
        self,
        rows: list[tuple[Any, ...]],
        columns: list[str],
        error: Exception | None = None,
    ) -> None:
        self.description = [(name,) for name in columns]
        self._rows = list(rows)
        self._error = error
        self.executed: list[str] = []
        self.fetch_sizes: list[int] = []
        self.closed = False

    def execute(self, query: str) -> None:
        if self._error is not None:
            raise self._error

        self.executed.append(query)

    def fetchmany(self, size: int) -> list[tuple[Any, ...]]:
        self.fetch_sizes.append(size)

        batch = self._rows[:size]
        del self._rows[:size]

        return batch

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self._cursor

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_driver(monkeypatch: pytest.MonkeyPatch):
    """Install a fake mariadb module and expose what it was asked to do."""

    state: dict[str, Any] = {}

    def install(rows=None, columns=None, execute_error=None):
        cursor = FakeCursor(
            rows if rows is not None else [(1, "a")],
            columns if columns is not None else ["id", "label"],
            execute_error,
        )
        connection = FakeConnection(cursor)

        def connect(**kwargs):
            state["kwargs"] = kwargs
            return connection

        driver = type(
            "FakeMariaDB", (), {"connect": staticmethod(connect), "Error": FakeError}
        )
        monkeypatch.setitem(sys.modules, "mariadb", driver)

        state["cursor"] = cursor
        state["connection"] = connection

        return state

    return install


def build_config(**overrides) -> MariaDBConfig:
    settings: dict[str, Any] = {
        "host": "db.internal",
        "user": "reader",
        "password": "secret",
        "database": "analytics",
    }
    settings.update(overrides)

    return MariaDBConfig(**settings)


class TestConnection:
    def test_the_configured_settings_reach_the_driver(self, fake_driver, table):
        state = fake_driver()

        list(MariaDBConnector(build_config()).extract(table))

        assert state["kwargs"] == {
            "host": "db.internal",
            "port": 3306,
            "user": "reader",
            "password": "secret",
            "database": "analytics",
        }

    def test_a_custom_port_is_used(self, fake_driver, table):
        state = fake_driver()

        list(MariaDBConnector(build_config(port=3307)).extract(table))

        assert state["kwargs"]["port"] == 3307

    def test_the_cursor_and_the_connection_are_closed(self, fake_driver, table):
        state = fake_driver()

        list(MariaDBConnector(build_config()).extract(table))

        assert state["cursor"].closed
        assert state["connection"].closed

    def test_they_are_closed_even_when_the_query_fails(self, fake_driver, table):
        """A failure must not leak the connection."""

        state = fake_driver(execute_error=FakeError("syntax error"))

        with pytest.raises(FakeError):
            list(MariaDBConnector(build_config()).extract(table))

        assert state["cursor"].closed
        assert state["connection"].closed


class TestExtraction:
    def test_the_generated_select_is_executed(self, fake_driver, table):
        state = fake_driver()

        list(MariaDBConnector(build_config()).extract(table))

        (query,) = state["cursor"].executed

        assert "SELECT" in query
        assert "FROM" in query
        assert "events" in query

    def test_rows_become_dictionaries_keyed_by_column_name(self, fake_driver, table):
        fake_driver(rows=[(1, "a"), (2, "b")], columns=["id", "label"])

        records = list(MariaDBConnector(build_config()).extract(table))

        assert records == [{"id": 1, "label": "a"}, {"id": 2, "label": "b"}]

    def test_rows_are_fetched_in_chunks_of_the_requested_size(self, fake_driver, table):
        state = fake_driver(rows=[(i, "x") for i in range(10)], columns=["id", "label"])

        list(MariaDBConnector(build_config()).extract(table, fetch_size=4))

        assert state["cursor"].fetch_sizes[0] == 4
        assert all(size == 4 for size in state["cursor"].fetch_sizes)

    def test_every_row_is_yielded_across_chunks(self, fake_driver, table):
        fake_driver(rows=[(i, "x") for i in range(10)], columns=["id", "label"])

        records = list(MariaDBConnector(build_config()).extract(table, fetch_size=4))

        assert len(records) == 10
        assert [record["id"] for record in records] == list(range(10))

    def test_an_empty_table_yields_nothing(self, fake_driver, table):
        fake_driver(rows=[], columns=["id", "label"])

        assert list(MariaDBConnector(build_config()).extract(table)) == []

    def test_nothing_is_queried_until_the_records_are_consumed(
        self, fake_driver, table
    ):
        state = fake_driver()

        records = MariaDBConnector(build_config()).extract(table)

        assert "kwargs" not in state

        next(records)

        assert "kwargs" in state


class TestOptionalDriver:
    """The driver is an optional dependency, so its absence must be handled."""

    def test_the_connector_can_be_built_without_the_driver(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "mariadb", None)

        assert MariaDBConnector(build_config()) is not None

    def test_extracting_without_the_driver_explains_how_to_install_it(
        self, monkeypatch, table
    ):
        monkeypatch.setitem(sys.modules, "mariadb", None)

        with pytest.raises(RuntimeError, match="uv sync --extra mariadb"):
            list(MariaDBConnector(build_config()).extract(table))

    def test_the_package_imports_without_the_driver(self):
        """The whole point of the optional dependency.

        Run in a subprocess with the driver blocked, since the package is
        already imported in this one.
        """

        subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.modules['mariadb'] = None; import ingestion_engine",
            ],
            check=True,
        )
