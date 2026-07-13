from collections.abc import Iterator

import requests

from src.models.schema import TableConfig, Column
from src.database.clickhouse import get_client 

def json_connector(url: str) -> Iterator[dict]:
    response = requests.get(url=url, timeout=30).json()
    response.raise_for_status()

    for row in response:
        print("Nuova Riga")
        yield row



def dict_normalizer(row: dict , table: TableConfig) -> tuple:
    output = []
    for col in table.columns:
        current = row 
        for part in col.source_address.split("."):
            current = current[part]
        output.append(current)
    return tuple(output)


def batcher(rows, batch_amount: int) :
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == batch_amount:
            print(batch)
            yield batch 
            batch = []
            print("Batch_ended")
    if batch:
        yield batch

client = get_client()
client.insert
def clickhouse_loader(client, table: TableConfig, batch: list[tuple]) -> None:
    table_name = table.name
    client.insert(table=table_name, data=batch)



if __name__ == "__main__":
    from src.models.users import users
    url = "https://jsonplaceholder.typicode.com/users"
    client = get_client()
    gen = json_connector(url=url)
    # gen è un generator di dict
    rows = (
        dict_normalizer(row, users)
        for row in gen
    )
    # rows è un generator di tuple
    batches = batcher(rows=rows, batch_amount=3)

    for batch in batches:
        clickhouse_loader(client=client, table=users, batch=batch)
    