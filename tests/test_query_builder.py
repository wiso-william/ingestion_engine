"""Tests for QueryBuilder, including the identifier validation it enforces.

Table names, column names and column types are interpolated into the
statements, so the builder rejects anything that is not a plain identifier
instead of escaping it. These tests pin that contract down.
"""

import pytest

from ingestion_engine import Column, QueryBuilder, TableConfig


def build_table(
    name: str = "users",
    columns: list[Column] | None = None,
    order_by: str = "id",
) -> TableConfig:
    return TableConfig(
        name=name,
        columns=columns or [Column("id", "UInt64", "id")],
        order_by=order_by,
        source="test",
    )


class TestBuildDdl:
    def test_creates_the_table_with_the_declared_columns(self):
        table = build_table(
            columns=[
                Column("id", "UInt64", "id"),
                Column("label", "Nullable(String)", "label"),
            ]
        )

        ddl = QueryBuilder.build_ddl(table)

        assert "CREATE OR REPLACE TABLE users" in ddl
        assert "id UInt64" in ddl
        assert "label Nullable(String)" in ddl

    def test_uses_the_mergetree_engine_and_the_declared_sort_key(self):
        ddl = QueryBuilder.build_ddl(build_table(order_by="id"))

        assert "ENGINE = MergeTree()" in ddl
        assert "ORDER BY id" in ddl

    def test_a_sort_key_may_name_several_columns(self):
        """MergeTree accepts a composite sorting key, so the builder must too."""

        table = build_table(
            columns=[Column("id", "UInt64", "id"), Column("ts", "DateTime", "ts")],
            order_by="id, ts",
        )

        assert "ORDER BY id, ts" in QueryBuilder.build_ddl(table)

    def test_parameterized_column_types_are_accepted(self):
        """Types carry parameters, quotes and spaces, unlike identifiers."""

        table = build_table(
            columns=[
                Column("amount", "Decimal(10, 2)", "amount"),
                Column("ts", "DateTime64(3, 'UTC')", "ts"),
                Column("tags", "Array(String)", "tags"),
            ]
        )

        ddl = QueryBuilder.build_ddl(table)

        assert "amount Decimal(10, 2)" in ddl
        assert "ts DateTime64(3, 'UTC')" in ddl
        assert "tags Array(String)" in ddl


class TestBuildSelect:
    def test_reads_the_declared_columns_from_the_source_table(self):
        table = build_table(
            columns=[Column("id", "UInt64", "id"), Column("label", "String", "label")]
        )

        query = QueryBuilder.build_select(table)

        assert "SELECT" in query
        assert "id" in query
        assert "label" in query
        assert "FROM" in query
        assert "users" in query

    def test_only_the_configured_columns_are_selected(self):
        """A star select would break the positional insert downstream."""

        assert "*" not in QueryBuilder.build_select(build_table())


class TestIdentifierValidation:
    @pytest.mark.parametrize(
        "name",
        [
            "users; DROP TABLE users",
            "users--",
            "users`",
            'users"',
            "users users",
            "1users",
            "",
            "users)",
        ],
    )
    def test_a_table_name_that_is_not_an_identifier_is_rejected(self, name):
        with pytest.raises(ValueError, match="Invalid table name"):
            QueryBuilder.build_ddl(build_table(name=name))

    @pytest.mark.parametrize("name", ["id, 1 AS injected", "id)", "id;", ""])
    def test_a_column_name_that_is_not_an_identifier_is_rejected(self, name):
        with pytest.raises(ValueError, match="Invalid column name"):
            QueryBuilder.build_ddl(build_table(columns=[Column(name, "UInt8", "id")]))

    @pytest.mark.parametrize(
        "column_type",
        ["UInt8; DROP TABLE t", "UInt8 -- comment", "UInt8\nDROP", ""],
    )
    def test_a_column_type_carrying_statement_syntax_is_rejected(self, column_type):
        with pytest.raises(ValueError, match="Invalid type for column"):
            QueryBuilder.build_ddl(
                build_table(columns=[Column("id", column_type, "id")])
            )

    @pytest.mark.parametrize("order_by", ["id) --", "id; DROP TABLE t", ""])
    def test_a_sort_key_that_is_not_made_of_identifiers_is_rejected(self, order_by):
        with pytest.raises(ValueError, match="Invalid sort key column"):
            QueryBuilder.build_ddl(build_table(order_by=order_by))

    def test_build_select_validates_the_table_name_too(self):
        with pytest.raises(ValueError, match="Invalid table name"):
            QueryBuilder.build_select(build_table(name="users; DROP TABLE users"))

    def test_build_select_validates_column_names_too(self):
        table = build_table(columns=[Column("id, 1 AS injected", "UInt8", "id")])

        with pytest.raises(ValueError, match="Invalid column name"):
            QueryBuilder.build_select(table)

    def test_the_error_names_the_offending_value(self):
        """A configuration mistake has to be actionable from the message alone."""

        with pytest.raises(ValueError) as error:
            QueryBuilder.build_ddl(build_table(name="bad name"))

        assert "'bad name'" in str(error.value)

    @pytest.mark.parametrize("name", ["users", "_private", "a1", "snake_case_2"])
    def test_plain_identifiers_are_accepted(self, name):
        QueryBuilder.build_ddl(build_table(name=name))
        QueryBuilder.build_select(build_table(name=name))
