from src.models.schema import TableConfig

#r = requests.get("https://jsonplaceholder.typicode.com/users")


def normalize_json_v2(record: dict, table: TableConfig) -> tuple:
    row = []
    for column in table.columns:
        current = record 
        for part in column.source_address.split("."):
            current = current[part]
        
        row.append(current)
    return tuple(row)

if __name__ == "__main__":
    from src.connectors.mariadb import create_mariadb_connection_params, create_mariadb_connection, extract
    from src.models.esami_categorie import esami_categorie
    from src.sql_builder.query_builder import build_select

    from dotenv import load_dotenv
    import os

    load_dotenv()

    host = os.getenv("MARIADB_HOST")
    user = os.getenv("MARIADB_USER")
    password = os.getenv("MARIADB_PASSWORD")
    database = os.getenv("MARIADB_DATABASE")

    params = create_mariadb_connection_params(
        host=host,  
        user=user,
        password=password,
        database=database,
    )

    connection = create_mariadb_connection(params)

    query = build_select(table=esami_categorie)

    for record in extract(connection, query):
        print(normalize_json_v2(record, table=esami_categorie))