"""Demo pipeline loading a public REST API into ClickHouse.

Runnable with no configuration. Start the destination database:

    docker compose up -d

then run the pipeline from the repository root:

    uv run python -m examples.run_api_pipeline

The ClickHouse defaults below match docker-compose.yml, so a .env file is only
needed to point the pipeline at a different server.
"""

import logging
import os

import clickhouse_connect
from dotenv import load_dotenv

from examples.tables.users import users
from ingestion_engine import (
    APIConfig,
    APIConnector,
    ClickHouseConfig,
    ClickHouseLoader,
    DictNormalizer,
    TableConfig,
    run,
)
from ingestion_engine.config.log_config import setup_logging

API_URL = "https://jsonplaceholder.typicode.com/users"
BATCH_SIZE = 100

logger = logging.getLogger(__name__)


def build_clickhouse_config() -> ClickHouseConfig:
    """Read the destination settings, falling back to the compose defaults.

    Returns:
        ClickHouseConfig: Settings of the destination server.
    """

    return ClickHouseConfig(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8124")),
        user=os.getenv("CLICKHOUSE_USER", "root"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "root"),
        database=os.getenv("CLICKHOUSE_DATABASE", "ingestion"),
    )


def report(config: ClickHouseConfig, table: TableConfig) -> None:
    """Log what ended up in the destination table.

    Args:
        config: Settings of the destination server.
        table: Configuration of the table that was loaded.
    """

    client = clickhouse_connect.get_client(
        host=config.host,
        port=config.port,
        username=config.user,
        password=config.password,
        database=config.database,
    )

    try:
        count = client.command(f"SELECT count() FROM {table.name}")

        logger.info("Table %s now holds %s rows", table.name, count)

        for row in client.query(
            f"SELECT id, name, city FROM {table.name} ORDER BY id LIMIT 3"
        ).result_rows:
            logger.info("  %s", row)

    finally:
        client.close()


def main() -> None:
    """Extract the API users, load them into ClickHouse and report the result."""

    load_dotenv()
    setup_logging()

    clickhouse_config = build_clickhouse_config()

    run(
        connector=APIConnector(APIConfig(url=API_URL, headers={}, params={})),
        normalizer=DictNormalizer(),
        loader=ClickHouseLoader(clickhouse_config),
        table=users,
        batch_size=BATCH_SIZE,
    )

    report(clickhouse_config, users)


if __name__ == "__main__":
    main()
