from src.connectors.base import BaseConnector
from src.database.clickhouse import ClickHouseLoader
from src.normalizers.base import BaseNormalizer
from src.models.schema import TableConfig
from src.batchers.batcher import batcher

def run(
        connector: BaseConnector,
        normalizer: BaseNormalizer,
        loader: ClickHouseLoader,
        table: TableConfig,
        batch_size: int = 1000
) -> None:
    
    records = connector.extract(table)
    rows = normalizer.normalize(records, table)

    for batch in batcher(rows, batch_size):
        loader.load(table, batch)