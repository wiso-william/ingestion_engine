from dataclasses import dataclass

@dataclass
class Column:
    name: str 
    type: str 
    source_address: str

@dataclass 
class TableConfig:
    name: str
    columns: list[Column]
    order_by: str
    source: str
