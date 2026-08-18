from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from ingestion_engine.schema.table import TableConfig


class BaseConnector(ABC):
    """Interface implemented by every source connector.

    A connector wraps a single source system and exposes its records as an
    iterator of dictionaries, so that the rest of the pipeline stays
    independent from the source.

    Implementations may add further parameters to extract(), as long as they
    have a default value and the connector stays callable with the signature
    declared here, which is the one the pipeline relies on.
    """

    @abstractmethod
    def extract(self, table: TableConfig) -> Iterator[dict[str, Any]]:
        """Extract records from the source system.

        Args:
            table: Configuration defining the records to extract.

        Returns:
            Iterator[dict[str, Any]]: An iterator yielding records from the
                source system.
        """
        ...
