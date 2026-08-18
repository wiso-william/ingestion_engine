"""Tests for ClickHouseLoader and the way it manages its connection.

The loader opens one connection and reuses it, which is what keeps a load of
many batches from reconnecting once per insert. These tests cover that
lifecycle, since it is the part callers never see and therefore never check.
"""

import gc

from ingestion_engine import ClickHouseConfig, ClickHouseLoader


def build_loader(**overrides) -> ClickHouseLoader:
    settings = {
        "host": "localhost",
        "port": 8124,
        "user": "root",
        "password": "root",
        "database": "ingestion",
    }
    settings.update(overrides)

    return ClickHouseLoader(ClickHouseConfig(**settings))


class TestConnectionLifecycle:
    def test_building_a_loader_opens_no_connection(self, client_factory):
        """Constructing configuration must not reach out to the network."""

        build_loader()

        assert client_factory.opened == 0

    def test_the_first_operation_opens_the_connection(self, client_factory, table):
        build_loader().create_table(table)

        assert client_factory.opened == 1

    def test_every_later_operation_reuses_the_same_connection(
        self, client_factory, table
    ):
        loader = build_loader()

        loader.create_table(table)
        for _ in range(10):
            loader.load(table, [(1, "x")])

        assert client_factory.opened == 1

    def test_the_connection_stays_open_between_operations(self, client_factory, table):
        loader = build_loader()
        loader.load(table, [(1, "x")])

        assert client_factory.closed == 0

    def test_close_releases_the_connection(self, client_factory, table):
        loader = build_loader()
        loader.load(table, [(1, "x")])

        loader.close()

        assert client_factory.closed == 1

    def test_close_can_be_called_repeatedly(self, client_factory, table):
        loader = build_loader()
        loader.load(table, [(1, "x")])

        loader.close()
        loader.close()

        assert client_factory.closed == 1

    def test_close_on_a_loader_that_never_connected_is_harmless(self, client_factory):
        build_loader().close()

        assert client_factory.opened == 0

    def test_a_discarded_loader_releases_its_connection(self, client_factory, table):
        """Callers are not required to call close(), so nothing may leak."""

        loader = build_loader()
        loader.load(table, [(1, "x")])

        del loader
        gc.collect()

        assert client_factory.closed == 1

    def test_the_loader_reconnects_after_close(self, client_factory, table):
        loader = build_loader()

        loader.load(table, [(1, "x")])
        loader.close()
        loader.load(table, [(1, "x")])

        assert client_factory.opened == 2


class TestFailureHandling:
    def test_a_failing_insert_propagates(self, patch_client_factory, table):
        patch_client_factory([RuntimeError("connection lost")])
        loader = build_loader()

        try:
            loader.load(table, [(1, "x")])
        except RuntimeError as error:
            assert str(error) == "connection lost"
        else:
            raise AssertionError("the error was swallowed")

    def test_a_failing_operation_drops_the_connection(
        self, patch_client_factory, table
    ):
        """A broken connection must not be kept and reused."""

        factory = patch_client_factory([RuntimeError("connection lost")])
        loader = build_loader()

        try:
            loader.load(table, [(1, "x")])
        except RuntimeError:
            pass

        assert factory.closed == 1

    def test_the_next_operation_reconnects_after_a_failure(
        self, patch_client_factory, table
    ):
        """A loader whose connection dropped has to stay usable."""

        factory = patch_client_factory([RuntimeError("connection lost"), None])
        loader = build_loader()

        try:
            loader.load(table, [(1, "x")])
        except RuntimeError:
            pass

        loader.load(table, [(2, "y")])

        assert factory.opened == 2
        assert factory.clients[1].inserts == [("events", [(2, "y")])]


class TestOperations:
    def test_create_table_sends_the_generated_ddl(self, client_factory, table):
        build_loader().create_table(table)

        (ddl,) = client_factory.clients[0].commands

        assert "CREATE OR REPLACE TABLE events" in ddl
        assert "ORDER BY id" in ddl

    def test_load_inserts_the_rows_into_the_configured_table(
        self, client_factory, table
    ):
        rows = [(1, "a"), (2, "b")]

        build_loader().load(table, rows)

        assert client_factory.clients[0].inserts == [("events", rows)]

    def test_each_load_is_a_separate_insert(self, client_factory, table):
        loader = build_loader()

        loader.load(table, [(1, "a")])
        loader.load(table, [(2, "b")])

        assert len(client_factory.clients[0].inserts) == 2

    def test_an_invalid_table_configuration_never_reaches_the_server(
        self, client_factory
    ):
        """Validation happens while building the DDL, before it is executed."""

        from ingestion_engine import Column, TableConfig

        bad = TableConfig(
            name="events; DROP TABLE events",
            columns=[Column("id", "UInt64", "id")],
            order_by="id",
            source="test",
        )

        try:
            build_loader().create_table(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("the invalid name was accepted")

        assert client_factory.clients[0].commands == []


class TestConfiguration:
    def test_the_configured_settings_reach_the_driver(self, client_factory, table):
        loader = build_loader(host="ch.internal", port=9999, database="analytics")

        loader.create_table(table)

        (kwargs,) = client_factory.kwargs

        assert kwargs["host"] == "ch.internal"
        assert kwargs["port"] == 9999
        assert kwargs["database"] == "analytics"
        assert kwargs["username"] == "root"
        assert kwargs["password"] == "root"
