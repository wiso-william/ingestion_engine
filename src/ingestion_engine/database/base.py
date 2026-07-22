from abc import ABC, abstractmethod
from collections.abc import Iterable

from ingestion_engine.models.schema import TableConfig


class BaseLoader(ABC):

    @abstractmethod
    def create_table(self, table: TableConfig) -> None:
        ...

    @abstractmethod
    def load(
        self,
        table: TableConfig,
        rows: Iterable[tuple],
    ) -> None:
        ...