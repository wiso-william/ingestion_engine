from src.connectors.base import BaseConnector
from src.database.clickhouse import ClickHouseLoader
from src.models import esami_categorie
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

    loader.create_table(table)

    for batch in batcher(rows, batch_size):
        loader.load(table.name, batch)


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    from src.connectors.mariadb import MariaDBConnector
    from src.normalizers.normal import DictNormalizer
    from src.database.clickhouse import ClickHouseLoader
    from src.models.clickhouse import ClickHouseConfig
    from src.models.esami_categorie import esami_categorie
    from src.models.mariadb_config import MariaDBConfig

    load_dotenv()

    config = MariaDBConfig(
        host=os.getenv("MARIADB_HOST"),
        user=os.getenv("MARIADB_USER"),
        password=os.getenv("MARIADB_PASSWORD"),
        database=os.getenv("MARIADB_DATABASE")
    )

    connector = MariaDBConnector(config)
    normalizer = DictNormalizer()
    loader = ClickHouseLoader(ClickHouseConfig(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT")),
        user=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE")
    ))

    run(connector, normalizer, loader, esami_categorie, batch_size=1000)