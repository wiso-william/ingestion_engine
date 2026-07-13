from collections.abc import Iterable

import clickhouse_connect

from src.database.base import BaseLoader
from src.models.clickhouse import ClickHouseConfig
from src.models.schema import TableConfig
from src.sql_builder.query_builder import QueryBuilder


class ClickHouseLoader(BaseLoader):

    def __init__(self, config: ClickHouseConfig):
        self.config = config
    
    def __get_client(self):
        return clickhouse_connect.get_client(
            host=self.config.host,
            port=self.config.port,
            username=self.config.user,
            password=self.config.password,
            database=self.config.database,
    )

    def create_table(self, table: TableConfig)  -> None:
        client = self.__get_client()

        ddl = QueryBuilder.build_ddl(table)

        try:
            client.command(ddl)
        finally:
            client.close()

    def load(self, table: str, data: Iterable[tuple]) -> None:
        client = self.__get_client()
        try:
            client.insert(table=table, data=data)
        finally:
            client.close()


if __name__ == '__main__':
    import os 

    from src.sql_builder.query_builder import QueryBuilder

    from src.models.users import users

    ddl = QueryBuilder.build_ddl(users)

    loader = ClickHouseLoader(ClickHouseConfig(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT")),
        user=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE")
    ))
    loader.create_table(ddl)
