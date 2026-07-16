import logging

from src.connectors.base import BaseConnector
from src.database.clickhouse import ClickHouseLoader
from src.models import esami_categorie
from src.normalizers.base import BaseNormalizer
from src.models.schema import TableConfig
from src.batchers.batcher import batcher


logger = logging.getLogger(__name__)


def run(
        connector: BaseConnector,
        normalizer: BaseNormalizer,
        loader: ClickHouseLoader,
        table: TableConfig,
        batch_size: int = 1000
) -> None:
    logger.info("Starting data ingestion pipeline for table %s", table.name)

    try:
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