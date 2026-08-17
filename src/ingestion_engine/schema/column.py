from dataclasses import dataclass

@dataclass
class Column:
    """Definition of a single column of the destination table.

    Attributes:
        name: Column name in the destination table.
        type: Column type in the destination database, e.g. "Nullable(String)".
        source_address: Location of the value inside the source record. Nested
            keys are separated by dots, e.g. "address.geo.lat".
    """

    name: str
    type: str 
    source_address: str