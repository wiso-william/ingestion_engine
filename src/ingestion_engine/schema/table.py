from dataclasses import dataclass
from ingestion_engine.schema.column import Column

@dataclass 
class TableConfig:
    """Schema of a single table to ingest.

    Attributes:
        name: Table name, used both to query the source and to create the
            destination table.
        columns: Columns to extract, in the order they are loaded.
        order_by: Column used as sorting key of the destination table.
        source: Label identifying the source system the records come from.
    """

    name: str
    columns: list[Column]
    order_by: str
    source: str