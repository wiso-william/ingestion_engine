from collections.abc import Iterator

import clickhouse_connect

from src.models.clickhouse import ClickHouseConfig


class ClickHouseLoader:

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

    def create_table(self, ddl: str):
        client = self.__get_client()
        try:
            client.command(ddl)
        except Exception as e:
            print(f"Error occurred while creating table: {e}")
        finally:
            client.close()

    def insert(self, table: str, data: Iterator[list]):
        client = self.__get_client()
        try:
            client.insert(table=table, data=data)
        except Exception as e:
            print(f"Error occurred while inserting data: {e}")
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
