import logging
from collections.abc import Iterator

import mariadb

from ingestion_engine.config.mariadb_config import MariaDBConfig
from ingestion_engine.schema.table import TableConfig
from ingestion_engine.sql_builder.query_builder import QueryBuilder

from .base import BaseConnector

logger = logging.getLogger(__name__)


class MariaDBConnector(BaseConnector):
    """Connector extracting records from a MariaDB database."""

    def __init__(self, config: MariaDBConfig) -> None:
        self.config = config

    def _create_connection(self) -> mariadb.Connection:
        """Open a connection to the configured MariaDB database.

        Returns:
            mariadb.Connection: An open connection to the database.

        Raises:
            mariadb.Error: If the connection cannot be established.
        """

        logger.info(
            "Connecting to MariaDB (%s:%d/%s)",
            self.config.host,
            self.config.port,
            self.config.database,
        )

        return mariadb.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
        )

    def extract(
        self,
        table: TableConfig,
        fetch_size: int = 5000,
    ) -> Iterator[dict]:
        """Extract records from a MariaDB table in batches.

        Args:
            table: Configuration defining the table to extract.
            fetch_size: Number of rows fetched from the database per batch.

        Yields:
            dict: Records extracted from the table.

        Raises:
            mariadb.Error: If the extraction fails.
        """

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
                    yield dict(zip(columns, row, strict=True))

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
