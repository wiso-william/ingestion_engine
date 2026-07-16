from collections.abc import Iterator
import logging

import mariadb

from .base import BaseConnector
from src.models.schema import TableConfig
from src.models.mariadb_config import MariaDBConfig
from src.sql_builder.query_builder import QueryBuilder


logger = logging.getLogger(__name__)


class MariaDBConnector(BaseConnector):

    def __init__(self, config: MariaDBConfig):
        self.config = config

    def _create_connection(self) -> mariadb.Connection:
        logger.info(
            "Connecting to MariaDB (%s/%s)",
            self.config.host,
            self.config.database,
        )

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

        connection = None
        cursor = None

        try:
            connection = self._create_connection()
            cursor = connection.cursor()

            query = QueryBuilder.build_select(table)

            logger.info("Extracting table %s", table.name)
            logger.debug("Executing query:\n%s", query)

            cursor.execute(query)

            columns = [column[0] for column in cursor.description]

            while True:
                rows = cursor.fetchmany(fetch_size)

                if not rows:
                    break

                logger.debug("Fetched %d rows", len(rows))

                for row in rows:
                    yield dict(zip(columns, row))

            logger.info("Extraction completed for %s", table.name)

        except mariadb.Error:
            logger.exception(
                "Failed to extract table %s",
                table.name,
            )
            raise

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

            logger.debug("MariaDB connection closed")