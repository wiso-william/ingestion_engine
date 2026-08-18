# Ingestion Engine

[![CI](https://github.com/wiso-william/ingestion_engine/actions/workflows/ci.yml/badge.svg)](https://github.com/wiso-william/ingestion_engine/actions/workflows/ci.yml)

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
* Type-safe configuration using dataclasses, checked with mypy in `strict` mode
* Annotations exported to consumers through a `py.typed` marker
* Public API designed through `__init__.py`
* Easy integration with orchestration frameworks such as Apache Airflow

---

## Requirements

* Python 3.10 or newer
* [uv](https://docs.astral.sh/uv/)
* Docker, to run the ClickHouse the examples load into

The MariaDB connector additionally needs MariaDB Connector/C on the system,
since the `mariadb` driver ships wheels for Windows only and is built from
source everywhere else. On Debian and Ubuntu:

```bash
sudo apt-get install libmariadb-dev
```

The API example does not need it, so it stays runnable everywhere.

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
    connector=APIConnector(
        APIConfig(url="https://example.com/records", headers={}, params={})
    ),
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

Note that `users.py` declares the API's `geo.lat` as `Float64` even though the
endpoint returns it as a JSON string: the driver parses numeric strings into the
declared numeric type. Limitations sets out exactly what is and is not
converted.

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

Linting, formatting and type checking are configured in `pyproject.toml`:

```bash
uv run ruff check .
```

```bash
uv run ruff format --check .
```

```bash
uv run mypy
```

mypy runs in `strict` mode over `src`, `examples` and `tests`. Test functions
are exempt from the annotation requirement, since they are identified by their
name rather than their signature, but the doubles they use are not.

The package ships a `py.typed` marker, so these annotations are not only checked
here: they are honoured by the type checker of anyone who installs the package.

CI runs all of it on every push and pull request: the suite across Python 3.10
to 3.13, the ruff checks, mypy, a lockfile check and a package build. The ruff
and mypy versions come from the lockfile, so a new release of either cannot
break the build on its own.

---

## Design Goals

* Keep the ingestion logic independent from orchestration.
* Make connectors, loaders, and normalizers easily replaceable.
* Provide a clean and stable public API.
* Support orchestration tools without coupling business logic to them.

---

## Limitations

These are deliberate boundaries rather than missing pieces. Each one is a
decision about what belongs in an ingestion tool and what belongs downstream.

### Full refresh only

`build_ddl` generates a `CREATE OR REPLACE TABLE`, so every run rebuilds the
destination table and discards the rows it held. There is no incremental load,
no change data capture and no upsert.

What this buys is a run that is idempotent and keeps no state: it either
rebuilds the table or fails, and there is never a partial result to reason
about. Incremental loading needs watermarks, deletion handling and somewhere to
keep them, which is a different tool rather than a flag on this one.

### Values are converted by the driver, not by the framework

A column's type describes the destination column: it is what goes into the
`CREATE TABLE`. The normalizer resolves the *shape* of a record, walking
`source_address` into nested keys, and never touches a value.

Whether a value is then accepted is decided by the ClickHouse driver, which
converts some mismatches and refuses others:

| Declared type | Value coming from the source | Result |
| --- | --- | --- |
| `Float64`, `UInt64`, `Decimal(p, s)` | a numeric string, e.g. `"-37.3159"` | converted |
| an integer type | a float, e.g. `3.7` | converted, truncated to `3` |
| an integer type | a string that is not an integer, e.g. `"3.7"` | rejected |
| an integer type | a value outside its range, e.g. `130` for `Int8` | rejected |
| `Date`, `DateTime`, `DateTime64` | a string, e.g. `"2024-01-15 10:00:00"` | rejected, a `date` or `datetime` object is required |
| `String` | anything that is not a string | rejected |

This is why `examples/tables/users.py` declares the API's `geo.lat` as `Float64`
even though the endpoint returns it as a JSON string: the destination ends up
holding a real float.

One consequence is worth knowing before relying on it. The driver decides how to
treat a whole column from its **first non-null value**, so the order of the rows
matters:

```text
Float64  <-  ["1.5", 2.5]   loads
Float64  <-  [1.5, "2.5"]   is rejected
```

A source that returns a number sometimes as text and sometimes as a number will
therefore succeed or fail depending on which record arrives first.

The framework adds no conversion layer of its own on top of this, and that is
deliberate. Reshaping a record is ingestion; deciding what its values should
become is transformation, and belongs in staging. Declare the type the
destination should hold, keep the source's own quirks in mind, and let anything
beyond that happen downstream.

### One table per run

`run` ingests a single `TableConfig`. Loading several tables, in whatever order
and with whatever parallelism, is left to the caller, for the reason given under
Design Goals: orchestration stays outside the framework.

### No retries

A failed request or a dropped connection fails the pipeline. Retrying, backing
off and alerting belong to whatever schedules the run, so the framework stays
out of them.

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
- Continuous integration
- Linting with ruff
- Static type checking with mypy
```

## License
This project is intended for educational purposes and personal experimentation with modern Data Engineering practices.
