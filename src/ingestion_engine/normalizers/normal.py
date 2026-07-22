from collections.abc import Iterator

from .base import BaseNormalizer
from ingestion_engine.models.schema import TableConfig

class DictNormalizer(BaseNormalizer):
    def normalize(
        self,
        records: Iterator[dict],
        table: TableConfig
    ) -> Iterator[tuple]:
        for record in records:
            row = []
            for column in table.columns:
                current = record 
                for part in column.source_address.split("."):
                    current = current[part]
                
                row.append(current)
            yield tuple(row)