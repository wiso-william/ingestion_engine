from dotenv import load_dotenv
import os

from ingestion_engine.connectors.mariadb import MariaDBConnector
from ingestion_engine.database.clickhouse import ClickHouseLoader
from ingestion_engine.log_config.config import setup_logging
from ingestion_engine.models.clickhouse import ClickHouseConfig
from examples.tables.esami_categorie import esami_categorie
from ingestion_engine.models.mariadb_config import MariaDBConfig
from ingestion_engine.normalizers.normal import DictNormalizer
from ingestion_engine.process_data.pipeline import run


load_dotenv()
setup_logging()

BATCH_SIZE = 10000

mariadb_config = MariaDBConfig(
    host=os.getenv("MARIADB_HOST"),
    user=os.getenv("MARIADB_USER"),
    password=os.getenv("MARIADB_PASSWORD"),
    database=os.getenv("MARIADB_DATABASE")
)

clickhouse_config = ClickHouseConfig(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT")),
        user=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE")
    )


connector = MariaDBConnector(mariadb_config)
normalizer = DictNormalizer()
loader = ClickHouseLoader(clickhouse_config)


run(
    connector=connector,
    normalizer=normalizer,
    loader=loader,
    batch_size=BATCH_SIZE,
    table=esami_categorie,
)