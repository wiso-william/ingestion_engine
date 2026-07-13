from collections.abc import Iterator

import mariadb

from .base import BaseConnector
from src.models.schema import TableConfig
from src.models.mariadb_config import MariaDBConfig
from src.sql_builder.query_builder import QueryBuilder


class MariaDBConnector(BaseConnector):

    def __init__(self, config: MariaDBConfig):
        self.config = config

    def _create_connection(self) -> mariadb.Connection:
        return mariadb.connect(
            host=self.config.host,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
        )

    def extract(
        self,
        table: TableConfig,
        fetch_size: int = 5000,
    ) -> Iterator[dict]:

        try:
            connection = self._create_connection()

            cursor = connection.cursor()

            query = QueryBuilder.build_select(table)

            cursor.execute(query)

            columns = [c[0] for c in cursor.description]

            while True:

                rows = cursor.fetchmany(fetch_size)

                if not rows:
                    break

                for row in rows:
                    yield dict(zip(columns, row))

        finally:
            cursor.close()
            connection.close()