from src.models.users import users
from src.models.schema import TableConfig

def build_ddl(table: TableConfig) -> str:
    columns = ",\n".join(
        f"{c.name} {c.type}"
        for c in table.columns
    )

    return f"""
CREATE TABLE IF NOT EXISTS {table.name}
(
{columns}
)
ENGINE = MergeTree()
ORDER BY {table.order_by}
    """


def build_select(table: TableConfig) -> str:
    columns = ",\n    ".join(
        f"{col.name}"
        for col in table.columns
    )

    select = f"""
SELECT 
    {columns}
FROM 
    {table.name}
"""
    
    return select