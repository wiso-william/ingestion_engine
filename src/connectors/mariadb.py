from collections.abc import Iterator

import mariadb


def create_mariadb_connection_params(
    host: str,
    user: str,
    password: str,
    database: str,
) -> dict:
    return {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
    }


def create_mariadb_connection(params: dict) -> mariadb.Connection:
    return mariadb.connect(**params)


def extract(
    connection: mariadb.Connection,
    query: str,
    fetch_size: int = 1000,
) -> Iterator[dict]:

    cursor = connection.cursor()

    cursor.execute(query)

    columns = [column[0] for column in cursor.description]

    while True:

        rows = cursor.fetchmany(fetch_size)

        if not rows:
            break

        for row in rows:
            yield dict(zip(columns, row))

    cursor.close()



if __name__ == "__main__":
    from dotenv import load_dotenv
    from src.sql_renderer import build_select
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

    query = "SELECT * FROM esami_categorie"

    for record in extract(connection, query):
        print(record)