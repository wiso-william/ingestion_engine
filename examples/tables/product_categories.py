from ingestion_engine import Column, TableConfig

product_categories = TableConfig(
    name="product_categories",
    columns=[
        Column("id", "UInt8", "id"),
        Column("name", "String", "name"),
        Column("short_name", "String", "short_name"),
        Column("department", "Nullable(String)", "department"),
    ],
    order_by="id",
    source="mariadb__product_categories",
)
