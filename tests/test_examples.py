"""Tests guarding the shipped examples.

The examples are the first thing anyone runs, so a broken one is worse than a
missing feature. These tests check that each table configuration is valid and
that every declared type is a type ClickHouse actually knows, which is what a
typo or a made up type would trip on.
"""

from pathlib import Path

import pytest
from clickhouse_connect.datatypes.registry import get_from_name

from examples.tables.product_categories import product_categories
from examples.tables.users import users
from ingestion_engine import QueryBuilder, TableConfig


EXAMPLE_TABLES = [product_categories, users]
EXAMPLE_IDS = [table.name for table in EXAMPLE_TABLES]

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLICKHOUSE_VARIABLES = (
    "CLICKHOUSE_HOST",
    "CLICKHOUSE_PORT",
    "CLICKHOUSE_USER",
    "CLICKHOUSE_PASSWORD",
    "CLICKHOUSE_DATABASE",
)


@pytest.mark.parametrize("table", EXAMPLE_TABLES, ids=EXAMPLE_IDS)
class TestExampleTables:
    def test_declares_at_least_one_column(self, table: TableConfig):
        assert table.columns

    def test_the_ddl_can_be_built(self, table: TableConfig):
        assert "CREATE OR REPLACE TABLE" in QueryBuilder.build_ddl(table)

    def test_the_select_can_be_built(self, table: TableConfig):
        assert "SELECT" in QueryBuilder.build_select(table)

    def test_every_declared_type_is_a_real_clickhouse_type(self, table: TableConfig):
        for column in table.columns:
            get_from_name(column.type)

    def test_the_sort_key_is_one_of_the_declared_columns(self, table: TableConfig):
        names = {column.name for column in table.columns}
        key_columns = {part.strip() for part in table.order_by.split(",")}

        assert key_columns <= names

    def test_column_names_are_unique(self, table: TableConfig):
        names = [column.name for column in table.columns]

        assert len(names) == len(set(names))


class TestUsersTable:
    def test_the_api_coordinates_are_declared_as_strings(self):
        """jsonplaceholder returns geo.lat and geo.lng as JSON strings.

        The framework does not cast values, so declaring them numeric makes the
        demo fail on the insert. This pins the fix in place.
        """

        types = {column.name: column.type for column in users.columns}

        assert types["lat"] == "String"
        assert types["lng"] == "String"

    def test_nested_fields_are_addressed_with_dots(self):
        addresses = {column.source_address for column in users.columns}

        assert "address.geo.lat" in addresses
        assert "company.catchPhrase" in addresses


class TestApiDemo:
    def test_the_demo_targets_a_public_endpoint_over_https(self):
        from examples.run_api_pipeline import API_URL

        assert API_URL.startswith("https://")

    def test_it_runs_without_any_environment_variable(self, monkeypatch):
        """The demo has to run with no .env, or it is not a demo."""

        for variable in CLICKHOUSE_VARIABLES:
            monkeypatch.delenv(variable, raising=False)

        from examples.run_api_pipeline import build_clickhouse_config

        config = build_clickhouse_config()

        assert config.host == "localhost"

    def test_the_defaults_match_the_compose_file(self, monkeypatch):
        """The two drift apart silently, so they are compared here.

        docker-compose.yml is read as text rather than parsed, to avoid pulling
        a YAML dependency into the test suite for four lookups.
        """

        for variable in CLICKHOUSE_VARIABLES:
            monkeypatch.delenv(variable, raising=False)

        from examples.run_api_pipeline import build_clickhouse_config

        config = build_clickhouse_config()
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        assert f"CLICKHOUSE_DB: {config.database}" in compose
        assert f"CLICKHOUSE_USER: {config.user}" in compose
        assert f"CLICKHOUSE_PASSWORD: {config.password}" in compose
        assert f'"{config.port}:8123"' in compose
