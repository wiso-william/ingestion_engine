from collections.abc import Iterator

from ingestion_engine.normalizers.base import BaseNormalizer
from ingestion_engine.schema.table import TableConfig

class DictNormalizer(BaseNormalizer):
    """Normalizer converting dictionary records into tuples."""

    def normalize(
        self,
        records: Iterator[dict],
        table: TableConfig
    ) -> Iterator[tuple]:
        """Convert records into tuples following the configured column order.

        Each value is looked up by walking the column source_address, whose
        dot-separated parts are treated as nested keys of the record.

        Args:
            records: Records extracted from the source system.
            table: Configuration defining the target table schema.

        Yields:
            tuple: Values of a single record, ordered as the table columns.

        Raises:
            KeyError: If a column source_address is missing from a record.
            TypeError: If a part of a source_address does not lead to a
                dictionary while keys are still left to traverse.
        """

        for record in records:
            row = []
            for column in table.columns:
                current = record 
                for part in column.source_address.split("."):
                    current = current[part]
                
                row.append(current)
            yield tuple(row)