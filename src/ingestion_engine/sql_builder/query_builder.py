from ingestion_engine.schema.table import TableConfig

class QueryBuilder:
    """Builds the SQL statements used by connectors and loaders."""

    @staticmethod
    def build_ddl(table: TableConfig) -> str:
        """Build the statement creating the destination table.

        The statement is a CREATE OR REPLACE, so an existing table with the
        same name is replaced together with its data.

        Args:
            table: Configuration defining the table schema.

        Returns:
            str: A CREATE OR REPLACE TABLE statement using the MergeTree engine.
        """

        columns = ",\n".join(
            f"{c.name} {c.type}"
            for c in table.columns
        )

        return f"""
        CREATE OR REPLACE TABLE {table.name}
        (
        {columns}
        )
        ENGINE = MergeTree()
        ORDER BY {table.order_by}
        """

    @staticmethod
    def build_select(table: TableConfig) -> str:
        """Build the statement extracting the configured columns from the source.

        Args:
            table: Configuration defining the source table and its columns.

        Returns:
            str: A SELECT statement reading the configured columns.
        """

        columns = ",\n    ".join(
            f"{col.name}"
            for col in table.columns
        )

        query = f"""
        SELECT 
            {columns}
        FROM 
            {table.name}
        """
        return query