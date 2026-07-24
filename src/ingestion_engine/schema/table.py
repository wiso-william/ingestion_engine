from dataclasses import dataclass
from ingestion_engine.schema.column import Column

@dataclass 
class TableConfig:
    name: str
    columns: list[Column]
    order_by: str
    source: str