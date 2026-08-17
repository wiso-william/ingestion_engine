from collections.abc import Iterable
import logging 

import clickhouse_connect

from ingestion_engine.config.clickhouse import ClickHouseConfig
from ingestion_engine.sql_builder.query_builder import QueryBuilder
from ingestion_engine.schema.table import TableConfig
from ingestion_engine.database.base import BaseLoader

    
logger = logging.getLogger(__name__)


class ClickHouseLoader(BaseLoader):
    """Loader creating and filling tables on a ClickHouse server.

    Every operation opens its own client and closes it afterwards, so the
    loader holds no connection between calls.
    """

    def __init__(self, config: ClickHouseConfig):
        self.config = config

    def __get_client(self):
        """Create a client connected to the configured ClickHouse database.

        Returns:
            clickhouse_connect.driver.Client: A client connected to the
                configured database.
        """

        logger.info("Connecting to ClickHouse (%s/%s)", 
                    self.config.host, 
                    self.config.database)

        return clickhouse_connect.get_client(
            host=self.config.host,
            port=self.config.port,
            username=self.config.user,
            password=self.config.password,
            database=self.config.database,
    )

    def create_table(self, table: TableConfig) -> None:
        """Create the destination table described by the configuration.

        The generated DDL replaces any existing table with the same name, so
        the data already loaded is discarded.

        Args:
            table: Configuration defining the table to create.

        Raises:
            Exception: If the DDL execution fails.
        """

        client = None

        try:
            client = self.__get_client()

            ddl = QueryBuilder.build_ddl(table)

            logger.info("Creating table %s", table.name)
            logger.debug("Executing DDL:\n%s", ddl)

            client.command(ddl)

            logger.info("Table %s created successfully", table.name)

        except Exception:
            logger.exception(
                "Failed to create table %s",
                table.name,
            )
            raise

        finally:
            if client is not None:
                client.close()

            logger.debug("ClickHouse client closed")

    def load(
        self,
        table: str,
        data: Iterable[tuple],
    ) -> None:
        """Insert normalized rows into an existing ClickHouse table.

        Args:
            table: Name of the target table.
            data: Normalized rows to insert, ordered as the table columns.

        Raises:
            Exception: If the insert fails.
        """

        client = None

        try:
            client = self.__get_client()

            logger.debug("Loading data into %s", table)

            client.insert(
                table=table,
                data=data,
            )

            logger.debug("Insert completed for %s", table)

        except Exception:
            logger.exception(
                "Failed inserting data into %s",
                table,
            )
            raise

        finally:
            if client is not None:
                client.close()

            logger.debug("ClickHouse client closed")