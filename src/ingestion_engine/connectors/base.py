from abc import ABC, abstractmethod
from collections.abc import Iterator

class BaseConnector(ABC):
    """Interface implemented by every source connector.

    A connector wraps a single source system and exposes its records as an
    iterator of dictionaries, so that the rest of the pipeline stays
    independent from the source.
    """

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