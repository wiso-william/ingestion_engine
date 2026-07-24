from ingestion_engine.schema.table import TableConfig

class QueryBuilder:

    @staticmethod
    def build_ddl(table: TableConfig) -> str:
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