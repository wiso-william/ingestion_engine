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

## Installation

Clone the repository and install the project in editable mode.

```bash
uv sync
```

or

```bash
uv pip install -e .
```

---

## Quick Start

```python
from ingestion_engine import (
    MariaDBConfig,
    ClickHouseConfig,
    MariaDBConnector,
    ClickHouseLoader,
    DictNormalizer,
    run,
)

from tables.my_table import my_table

connector = MariaDBConnector(mariadb_config)
loader = ClickHouseLoader(clickhouse_config)
normalizer = DictNormalizer()

run(
    connector=connector,
    loader=loader,
    normalizer=normalizer,
    table=my_table,
    batch_size=10000,
)
```

---

## Project Structure

```text
ingestion_engine/
├── examples/
├── scripts/
├── src/
│   └── ingestion_engine/
│       ├── batchers/
│       ├── config/
│       ├── connectors/
│       ├── database/
│       ├── log_config/
│       ├── normalizers/
│       ├── process_data/
│       ├── schema/
│       ├── sql_builder/
│       └── __init__.py
├── tests/
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

The `examples/` directory contains sample pipelines and table definitions demonstrating how to use the framework.

These files are **examples only** and are **not part of the public API**. Users are expected to define their own table configurations in their own projects.

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
```

## License
This project is intended for educational purposes and personal experimentation with modern Data Engineering practices.
