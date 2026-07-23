# Ingestion Engine

*A lightweight and extensible Python ingestion framework designed to extract data from multiple sources, normalize it into a common format, and load it into analytical databases.*

The project is built around a modular architecture that separates extraction, transformation, and loading, making it easy to extend with new connectors, normalizers, and loaders.

## Features
- Modular ETL architecture
- MariaDB connector
- REST API connector
- ClickHouse loader
- Configurable table schemas
- Batch processing
- Structured logging with automatic log rotation
- Type-safe configuration using dataclasses
- Easy integration with orchestration tools such as Apache Airflow

## Project Structure
```
src/
├── connectors/
├── database/
├── models/
├── normalizers/
├── process_data/
├── sql_builder/
├── batchers/
└── log_config/
```
## Architecture
```
                                                            Source
                                                               │
                                                               ▼
                                                        +--------------+
                                                        |  Connector   |
                                                        +--------------+
                                                               │
                                                               ▼
                                                        +--------------+
                                                        | Normalizer   |
                                                        +--------------+
                                                               │
                                                               ▼
                                                        +--------------+
                                                        |   Batcher    |
                                                        +--------------+
                                                               │
                                                               ▼
                                                        +--------------+
                                                        |    Loader    |
                                                        +--------------+
                                                               │
                                                               ▼
                                                         Destination DB
```

## Current Components
Connectors
MariaDB
REST API
Normalizers
Dictionary to tuple normalizer
Loaders
ClickHouse
Logging

The project uses Python's standard logging module with a centralized configuration.

Logs are written both to:

Console
Rotating log files (logs/ingestion.log)

This makes the project suitable for both local execution and orchestration environments such as Apache Airflow.

All of the models are examples, you can freely get rid of all except:
- schema.py (This would break everything)
- api_config.py
- mariadb_config.py

## Future evolutions
I'll implement Airflow Directly in this project as an orchestrator without using task mapping.

It will be a single DAG with multiple tasks with 1 task working on a single table written explicitly.

After a while I'll implement dynamic task mapping 

## License
This project is intended for educational purposes and personal experimentation with modern Data Engineering practices.
