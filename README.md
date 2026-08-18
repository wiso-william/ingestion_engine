# Ingestion Engine

*A lightweight and extensible Python ingestion framework designed to extract data from multiple sources, normalize them into a common format, and load them into analytical databases.*

The project is built around a modular architecture that cleanly separates extraction, normalization, batching, and loading. It is designed as an installable Python package with a simple public API, making it easy to extend with new connectors, normalizers, and loaders.

---

## Features

* Modern Python package using the `src` layout
* Modular ETL architecture
* MariaDB connector
* REST API connector
* ClickHouse loader
* Configurable table schemas
* Batch processing
* Structured logging with automatic log rotation
* Type-safe configuration using dataclasses
* Public API designed through `__init__.py`
* Easy integration with orchestration frameworks such as Apache Airflow

---

## Requirements

* Python 3.10 or newer
* [uv](https://docs.astral.sh/uv/)
* Docker, to run the ClickHouse the examples load into

The MariaDB connector additionally needs MariaDB Connector/C installed on the
system. The API example does not, so it stays runnable everywhere.

---

## Quick Start

The API example runs with no configuration. Start the destination database:

```bash
docker compose up -d
```

Install the project and run the pipeline from the repository root:

```bash
uv sync
```

```bash
uv run python -m examples.run_api_pipeline
```

It extracts the users of a public REST API, loads them into ClickHouse and
reports what landed there:

```text
... | INFO | ingestion_engine.process_data.pipeline | Starting data ingestion pipeline for table users
... | INFO | ingestion_engine.database.clickhouse   | Creating table users
... | INFO | ingestion_engine.connectors.api        | Extraction started, requesting data from https://jsonplaceholder.typicode.com/users
... | INFO | ingestion_engine.process_data.pipeline | Loading batch 1 with 10 rows into ClickHouse
... | INFO | examples.run_api_pipeline              | Table users now holds 10 rows
```

Rerunning it is safe: the destination table is replaced on every run.

---

## Usage

A pipeline is assembled from a connector, a normalizer, a loader and a table
configuration, then handed to `run`:

```python
from ingestion_engine import (
    APIConfig,
    APIConnector,
    ClickHouseConfig,
    ClickHouseLoader,
    DictNormalizer,
    run,
)

from my_tables import my_table

clickhouse_config = ClickHouseConfig(
    host="localhost",
    port=8124,
    user="root",
    password="root",
    database="ingestion",
)

run(
    connector=APIConnector(APIConfig(url="https://example.com/records", headers={}, params={})),
    normalizer=DictNormalizer(),
    loader=ClickHouseLoader(clickhouse_config),
    table=my_table,
    batch_size=10000,
)
```

Swapping the source means swapping the connector: nothing else in the pipeline
changes.

---

## Project Structure

```text
ingestion_engine/
├── examples/
│   ├── tables/
│   │   ├── product_categories.py
│   │   └── users.py
│   ├── run_api_pipeline.py
│   └── run_mariadb_pipeline.py
├── src/
│   └── ingestion_engine/
│       ├── batchers/
│       ├── config/
│       ├── connectors/
│       ├── database/
│       ├── normalizers/
│       ├── process_data/
│       ├── schema/
│       ├── sql_builder/
│       └── __init__.py
├── tests/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Architecture

```text
                                                         Source
                                                            │
                                                            ▼
                                                    +----------------+
                                                    |   Connector    |
                                                    +----------------+
                                                            │
                                                            ▼
                                                    +----------------+
                                                    |  Normalizer    |
                                                    +----------------+
                                                            │
                                                            ▼
                                                    +----------------+
                                                    |    Batcher     |
                                                    +----------------+
                                                            │
                                                            ▼
                                                    +----------------+
                                                    |     Loader     |
                                                    +----------------+
                                                            │
                                                            ▼
                                                     Destination DB
```

---

## Core Components

### Connectors

* MariaDB
* REST API

### Normalizers

* Dictionary → Tuple normalizer

### Loaders

* ClickHouse

### Schema

The framework provides generic schema definitions through:

* `TableConfig`
* `Column`

Users are expected to define their own table configurations in their projects using these classes.

### Configuration

The framework includes configuration objects for:

* `MariaDBConfig`
* `ClickHouseConfig`

implemented as Python dataclasses.

---

## Logging

The project uses Python's built-in `logging` module with a centralized configuration.

Logs are written to:

* Console
* Rotating log files (`logs/ingestion.log`)

making the framework suitable for both local execution and orchestration environments.

---

## Examples

The `examples/` directory contains runnable pipelines and the table definitions they use.

| Example | Needs | Notes |
| --- | --- | --- |
| `run_api_pipeline.py` | only `docker compose up -d` | Public REST API to ClickHouse. Start here. |
| `run_mariadb_pipeline.py` | a reachable MariaDB, `.env` filled in | Shows the second connector. Also needs MariaDB Connector/C on the system. |

Run them as modules from the repository root, e.g.
`uv run python -m examples.run_api_pipeline`.

A column type must match the type the source actually returns: the framework
normalizes the *shape* of a record, it does not cast its values. This is why
`users.py` declares the API's `geo.lat` as `String` and not as `Float64`.

These files are **examples only** and are **not part of the public API**. Users are expected to define their own table configurations in their own projects.

---

## Tests

```bash
uv run pytest
```

The suite needs no service running: the ClickHouse client, the MariaDB driver
and the HTTP layer are replaced by doubles, so what is under test is the
pipeline logic rather than the databases. It covers batching, normalization,
statement building and identifier validation, connection reuse, the mapping of
failures, and the shipped examples.

---

## Design Goals

* Keep the ingestion logic independent from orchestration.
* Make connectors, loaders, and normalizers easily replaceable.
* Provide a clean and stable public API.
* Support orchestration tools without coupling business logic to them.

---

## Roadmap

```text
Completed
---------

- Modular ingestion framework
- Installable Python package
- Public API
- ClickHouse loader
- MariaDB connector
- REST API connector
- Structured logging
- Test suite
```

## License
This project is intended for educational purposes and personal experimentation with modern Data Engineering practices.
