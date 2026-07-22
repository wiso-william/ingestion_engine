from abc import ABC, abstractmethod
from collections.abc import Iterator

class BaseConnector(ABC):

    @abstractmethod
    def extract(
        self,
        query: str
    ) -> Iterator[dict]:
        ...