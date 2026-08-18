from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from ingestion_engine.schema.table import TableConfig


class BaseLoader(ABC):
    """Interface implemented by every destination loader.

    A loader owns the destination database: it creates the target table and
    writes into it the rows produced by a normalizer.
    """

    @abstractmethod
    def create_table(self, table: TableConfig) -> None:
        """Create the destination table described by the configuration.

        Args:
            table: Configuration defining the table to create.
        """
        ...

    @abstractmethod
    def load(
        self,
        table: TableConfig,
        rows: Sequence[tuple[Any, ...]],
    ) -> None:
        """Insert normalized rows into the destination table.

        Args:
            table: Configuration defining the target table.
            rows: Normalized rows to insert.
        """
        ...
