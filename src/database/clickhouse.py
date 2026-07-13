import os

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT")),
        username=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE"),
    )


if __name__ == '__main__':
    from src.sql_renderer.ddl import build_ddl, build_select

    from src.models.users import users

    ddl = build_ddl(users)
    client = get_client()
    client.command(ddl)

    

