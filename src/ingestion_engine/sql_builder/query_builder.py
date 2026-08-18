import re

from ingestion_engine.schema.table import TableConfig


# Table and column names are interpolated into the statements, so they are
# restricted to plain unquoted identifiers: anything able to close an
# identifier and inject SQL is rejected instead of escaped.
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Column types are interpolated too, but they are not identifiers: they carry
# parameters, e.g. "Nullable(String)" or "DateTime64(3, 'UTC')". Only the
# characters those types need are allowed.
TYPE_PATTERN = re.compile(r"[A-Za-z0-9_(),' ]+")


def _validate_identifier(value: str, kind: str) -> str:
    """Check that a value is safe to interpolate as an SQL identifier.

    Args:
        value: The identifier to check.
        kind: What the identifier names, used in the error message.

    Returns:
        str: The identifier itself, unchanged.

    Raises:
        ValueError: If the value is not a plain unquoted identifier.
    """

    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid {kind}: {value!r}. Expected a plain identifier matching "
            f"{IDENTIFIER_PATTERN.pattern}"
        )

    return value


def _validate_type(value: str, column: str) -> str:
    """Check that a value is safe to interpolate as a column type.

    Args:
        value: The type to check.
        column: Name of the column the type belongs to, used in the error
            message.

    Returns:
        str: The type itself, unchanged.

    Raises:
        ValueError: If the type contains characters a type never needs.
    """

    if not TYPE_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid type for column {column!r}: {value!r}. Allowed "
            f"characters match {TYPE_PATTERN.pattern}"
        )

    return value


def _validate_sort_key(value: str) -> str:
    """Check the sorting key of the destination table.

    The key may name more than one column, separated by commas, since that is
    what a MergeTree ORDER BY accepts.

    Args:
        value: The sorting key to check.

    Returns:
        str: The sorting key, normalized to a comma separated list.

    Raises:
        ValueError: If any column of the key is not a plain identifier.
    """

    columns = [column.strip() for column in value.split(",")]

    for column in columns:
        _validate_identifier(column, "sort key column")

    return ", ".join(columns)


class QueryBuilder:
    """Builds the SQL statements used by connectors and loaders.

    Every table name, column name and column type is validated before being
    interpolated, so a malformed configuration fails with a ValueError instead
    of producing a statement that does something unintended.
    """

    @staticmethod
    def build_ddl(table: TableConfig) -> str:
        """Build the statement creating the destination table.

        The statement is a CREATE OR REPLACE, so an existing table with the
        same name is replaced together with its data.

        Args:
            table: Configuration defining the table schema.

        Returns:
            str: A CREATE OR REPLACE TABLE statement using the MergeTree engine.

        Raises:
            ValueError: If the table name, a column name, a column type or the
                sorting key is not valid.
        """

        name = _validate_identifier(table.name, "table name")
        order_by = _validate_sort_key(table.order_by)

        columns = ",\n".join(
            f"{_validate_identifier(c.name, 'column name')} "
            f"{_validate_type(c.type, c.name)}"
            for c in table.columns
        )

        return f"""
        CREATE OR REPLACE TABLE {name}
        (
        {columns}
        )
        ENGINE = MergeTree()
        ORDER BY {order_by}
        """

    @staticmethod
    def build_select(table: TableConfig) -> str:
        """Build the statement extracting the configured columns from the source.

        Args:
            table: Configuration defining the source table and its columns.

        Returns:
            str: A SELECT statement reading the configured columns.

        Raises:
            ValueError: If the table name or a column name is not valid.
        """

        name = _validate_identifier(table.name, "table name")

        columns = ",\n    ".join(
            _validate_identifier(col.name, "column name")
            for col in table.columns
        )

        query = f"""
        SELECT 
            {columns}
        FROM 
            {name}
        """
        return query
