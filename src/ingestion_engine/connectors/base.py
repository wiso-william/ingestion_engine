from abc import ABC, abstractmethod
from collections.abc import Iterator

class BaseConnector(ABC):

    @abstractmethod
    def extract(
        self,
        query: str
    ) -> Iterator[dict]:
        """Extract records from the source system.

        Args:
            query: Query used to retrieve the records.

        Returns:
            Iterator[dict]: An iterator yielding records from the source system.
        """
        ...