from src.models.users import users
from src.models.schema import TableConfig, Column

#r = requests.get("https://jsonplaceholder.typicode.com/users")


def normalize_json(records: list[dict], table: TableConfig) -> list[tuple]:
    rows = []

    for record in records:

        row = []

        for column in table.columns:

            current = record

            for part in column.source_address.split("."):
                current = current[part]

            row.append(current)

        rows.append(tuple(row))

    return rows


def normalize_json_v2(record: dict, table: TableConfig) -> tuple:
    row = []
    for column in table.columns:
        current = record 
        for part in column.source_address.split("."):
            current = current[part]
        
        row.append(current)
    return tuple(row)

