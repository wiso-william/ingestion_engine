"""Example pipeline loading a MariaDB table into ClickHouse.

Unlike run_api_pipeline, this one needs a reachable MariaDB server: copy
.env.example to .env, fill in the connection settings, then run it from the
repository root:

    uv run python -m examples.run_mariadb_pipeline

It also needs the mariadb driver, which builds against the MariaDB Connector/C
installed on the system. Start from run_api_pipeline if you only want to see
the framework work.
"""

import os

from dotenv import load_dotenv

from examples.tables.product_categories import product_categories
from ingestion_engine import (
    ClickHouseConfig,
    ClickHouseLoader,
    DictNormalizer,
    MariaDBConfig,
    MariaDBConnector,
    run,
)
from ingestion_engine.config.log_config import setup_logging


BATCH_SIZE = 10000


def main() -> None:
    """Extract the source table and load it into ClickHouse."""

    load_dotenv()
    setup_logging()

    mariadb_config = MariaDBConfig(
        host=os.environ["MARIADB_HOST"],
        port=int(os.getenv("MARIADB_PORT", "3306")),
        user=os.environ["MARIADB_USER"],
        password=os.environ["MARIADB_PASSWORD"],
        database=os.environ["MARIADB_DATABASE"],
    )

    clickhouse_config = ClickHouseConfig(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8124")),
        user=os.getenv("CLICKHOUSE_USER", "root"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "root"),
        database=os.getenv("CLICKHOUSE_DATABASE", "ingestion"),
    )

    run(
        connector=MariaDBConnector(mariadb_config),
        normalizer=DictNormalizer(),
        loader=ClickHouseLoader(clickhouse_config),
        table=product_categories,
        batch_size=BATCH_SIZE,
    )


if __name__ == "__main__":
    main()
