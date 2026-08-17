import logging

from ingestion_engine.database.clickhouse import ClickHouseLoader
from ingestion_engine.schema.table import TableConfig
from ingestion_engine.connectors.base import BaseConnector
from ingestion_engine.normalizers.base import BaseNormalizer
from ingestion_engine.batchers.batcher import batcher


logger = logging.getLogger(__name__)


def run(
        connector: BaseConnector,
        normalizer: BaseNormalizer,
        loader: ClickHouseLoader,
        table: TableConfig,
        batch_size: int = 1000
) -> None:
    """Run the ingestion pipeline for a single table.

    Extracts the records from the source, normalizes them, creates the
    destination table and loads the rows batch by batch.

    Args:
        connector: Connector extracting the records from the source system.
        normalizer: Normalizer converting the records into loadable rows.
        loader: Loader creating the destination table and inserting the rows.
        table: Configuration defining the table to ingest.
        batch_size: Maximum number of rows sent to the loader per insert.

    Raises:
        RuntimeError: If any stage of the pipeline fails.
    """

    logger.info("Starting data ingestion pipeline for table %s", table.name)

    try:
        # Extraction and normalization are lazy: nothing is read from the
        # source until the batches are consumed below.
        records = connector.extract(table)
        rows = normalizer.normalize(records, table)

        loader.create_table(table)

        batch_count = 0
        row_count = 0

        for batch in batcher(rows, batch_size):
            batch_count += 1
            row_count += len(batch)

            logger.info("Loading batch %d with %d rows into ClickHouse", batch_count, len(batch))

            loader.load(table.name, batch)

        logger.info("Data ingestion pipeline completed successfully for table %s", table.name) 

    except Exception as e:
        logger.exception("Data ingestion pipeline failed for table %s", table.name)
        raise RuntimeError(f"Data ingestion pipeline failed for table {table.name}") from e