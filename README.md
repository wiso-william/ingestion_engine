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
* Type-safe configuration using dataclasses
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

Note that `users.py` declares the API's `geo.lat` as `String` and not as
`Float64`: the endpoint returns it as a JSON string, and types are declared
rather than converted. See Limitations.

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

Linting and formatting are handled by ruff, configured in `pyproject.toml`:

```bash
uv run ruff check .
```

```bash
uv run ruff format --check .
```

CI runs all of it on every push and pull request: the suite across Python 3.10
to 3.13, the two ruff checks above, a lockfile check and a package build. The
ruff version comes from the lockfile, so a new release cannot break the build
on its own.

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

### Types are declared, not converted

A column's type describes the destination column: it is what goes into the
`CREATE TABLE`. The value arriving from the source must already be of a type the
destination accepts. The normalizer resolves the *shape* of a record, walking
`source_address` into nested keys, and never casts a value.

Declaring `Float64` for a field the source delivers as the string `"-37.3159"`
therefore fails on insert instead of being quietly parsed. This is why
`examples/tables/users.py` declares the API's `geo.lat` as `String`.

Automatic conversion driven by the declared type was designed and then
deliberately rejected, for four reasons:

* **It would be the one implicit thing in an explicit schema.** Columns are
  declared by hand precisely so that nothing is inferred or hidden. Parsing a
  string into a number *because* the column happens to say `Float64` puts back
  the implicitness the explicit declaration exists to remove.
* **Changing a value's type is transformation, not ingestion.** The same
  reasoning that keeps `Nullable(String)` cleanup out of this stage keeps string
  parsing out of it. Ingestion loads the source faithfully; staging reshapes it.
* **It would almost never be reached.** A SQL driver already returns typed
  objects: MariaDB Connector/Python returns `int` for `INT`, `Decimal` for
  `DECIMAL` and `datetime` for `DATETIME`, so a database source never presents
  the problem. Only loosely typed sources do, JSON above all, where a number can
  arrive as text.
* **Conversions that lose information have to fail, and they already do.** The
  ClickHouse driver rejects `3.7` for a `UInt8` column, `130` for `Int8` and
  `256` for `UInt8`. A cast placed in front of it could only weaken that
  guarantee, never strengthen it.

Declare the type the source actually delivers, and convert in staging.

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
```

## License
This project is intended for educational purposes and personal experimentation with modern Data Engineering practices.
