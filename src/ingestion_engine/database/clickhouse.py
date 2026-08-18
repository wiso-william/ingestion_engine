from __future__ import annotations

from collections.abc import Iterable
import logging
import weakref

import clickhouse_connect
from clickhouse_connect.driver import Client

from ingestion_engine.config.clickhouse import ClickHouseConfig
from ingestion_engine.sql_builder.query_builder import QueryBuilder
from ingestion_engine.schema.table import TableConfig
from ingestion_engine.database.base import BaseLoader


logger = logging.getLogger(__name__)


class ClickHouseLoader(BaseLoader):
    """Loader creating and filling tables on a ClickHouse server.

    The connection is opened by the first operation and reused by the ones
    that follow, so loading a table costs a single connection no matter how
    many batches it takes. Callers do not have to manage it: close() releases
    it explicitly, and it is released anyway once the loader is garbage
    collected or the interpreter exits.

    A failing operation drops the connection before raising, so a loader whose
    connection broke reconnects on the next call instead of staying unusable.
    """

    def __init__(self, config: ClickHouseConfig):
        self.config = config
        self._client: Client | None = None
        self._finalizer: weakref.finalize | None = None

    @staticmethod
    def _close_client(client: Client) -> None:
        """Close a client.

        Kept static so that the finalizer holds no reference to the loader,
        which would stop the loader from ever being garbage collected.

        Args:
            client: The client to close.
        """

        client.close()

        logger.debug("ClickHouse client closed")

    def _get_client(self) -> Client:
        """Return the client every operation runs on, connecting if needed.

        The client is created on the first call and cached, so the following
        calls reuse the same connection.

        Returns:
            Client: A client connected to the configured database.
        """

        if self._client is not None:
            return self._client

        logger.info(
            "Connecting to ClickHouse (%s/%s)",
            self.config.host,
            self.config.database,
        )

        self._client = clickhouse_connect.get_client(
            host=self.config.host,
            port=self.config.port,
            username=self.config.user,
            password=self.config.password,
            database=self.config.database,
        )

        self._finalizer = weakref.finalize(
            self,
            self._close_client,
            self._client,
        )

        return self._client

    def close(self) -> None:
        """Close the connection, if one is open.

        Safe to call more than once and safe to call on a loader that never
        connected: the following calls do nothing.
        """

        if self._finalizer is not None:
            self._finalizer()
            self._finalizer = None

        self._client = None

    def create_table(self, table: TableConfig) -> None:
        """Create the destination table described by the configuration.

        The generated DDL replaces any existing table with the same name, so
        the data already loaded is discarded.

        Args:
            table: Configuration defining the table to create.

        Raises:
            Exception: If the DDL execution fails.
        """

        try:
            client = self._get_client()

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
            self.close()
            raise

    def load(
        self,
        table: TableConfig,
        rows: Iterable[tuple],
    ) -> None:
        """Insert normalized rows into an existing ClickHouse table.

        Args:
            table: Configuration defining the target table.
            rows: Normalized rows to insert, ordered as the table columns.

        Raises:
            Exception: If the insert fails.
        """

        try:
            client = self._get_client()

            logger.debug("Loading data into %s", table.name)

            client.insert(
                table=table.name,
                data=rows,
            )

            logger.debug("Insert completed for %s", table.name)

        except Exception:
            logger.exception(
                "Failed inserting data into %s",
                table.name,
            )
            self.close()
            raise
