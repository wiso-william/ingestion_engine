from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from ingestion_engine.schema.table import TableConfig


class BaseNormalizer(ABC):
    """Interface implemented by every normalizer.

    A normalizer turns the records of a source into rows shaped like the
    destination table, so that a loader can insert them without knowing
    anything about the source format.
    """

    @abstractmethod
    def normalize(
        self, records: Iterator[dict[str, Any]], table: TableConfig
    ) -> Iterator[tuple[Any, ...]]:
        """Normalize source records according to the table configuration.

        Args:
            records: Records extracted from the source system.
            table: Configuration defining the target table schema.

        Yields:
            tuple: Normalized records ready to be loaded into the destination.
        """
        ...
