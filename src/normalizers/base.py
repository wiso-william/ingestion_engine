from abc import ABC, abstractmethod
from collections.abc import Iterator
from src.models.schema import TableConfig

class BaseNormalizer(ABC):

    @abstractmethod
    def normalize(
        self,
        records: Iterator[dict],
        table: TableConfig
    ) -> Iterator[tuple]:
        ...