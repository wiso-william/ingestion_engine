import logging
from collections.abc import Iterator
from types import ModuleType
from typing import Any, cast

from ingestion_engine.config.mariadb_config import MariaDBConfig
from ingestion_engine.schema.table import TableConfig
from ingestion_engine.sql_builder.query_builder import QueryBuilder

from .base import BaseConnector

logger = logging.getLogger(__name__)

DRIVER_MISSING = (
    "MariaDBConnector needs the mariadb driver, which is not installed. It is "
    "an optional dependency because it builds against MariaDB Connector/C: "
    "install that on the system, then the extra with "
    "`uv sync --extra mariadb`."
)


def load_driver() -> ModuleType:
    """Return the mariadb driver module.

    The driver is imported here rather than at module level so that importing
    ingestion_engine does not require MariaDB Connector/C, which the driver
    builds against. Only code that actually opens a connection needs it.

    Returns:
        ModuleType: The mariadb module.

    Raises:
        RuntimeError: If the driver is not installed, explaining how to add it.
    """

    try:
        import mariadb
    except ImportError as error:
        raise RuntimeError(DRIVER_MISSING) from error

    return cast(ModuleType, mariadb)


class MariaDBConnector(BaseConnector):
    """Connector extracting records from a MariaDB database.

    The driver is an optional dependency: constructing the connector always
    works, and the driver is required only once extraction starts.
    """

    def __init__(self, config: MariaDBConfig) -> None:
        self.config = config

    def _create_connection(self, driver: ModuleType) -> Any:  # noqa: ANN401
        """Open a connection to the configured MariaDB database.

        The return type is Any because the driver ships no annotations, so
        there is no connection type to refer to.

        Args:
            driver: The mariadb module, as returned by load_driver().

        Returns:
            An open connection to the database.

        Raises:
            Exception: The driver's own error if the connection fails.
        """

        logger.info(
            "Connecting to MariaDB (%s:%d/%s)",
            self.config.host,
            self.config.port,
            self.config.database,
        )

        return driver.connect(
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
    ) -> Iterator[dict[str, Any]]:
        """Extract records from a MariaDB table in batches.

        Args:
            table: Configuration defining the table to extract.
            fetch_size: Number of rows fetched from the database per batch.

        Yields:
            dict: Records extracted from the table.

        Raises:
            RuntimeError: If the mariadb driver is not installed.
            Exception: The driver's own error if the extraction fails.
        """

        driver = load_driver()

        connection = None
        cursor = None

        try:
            connection = self._create_connection(driver)
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

        except driver.Error:
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
