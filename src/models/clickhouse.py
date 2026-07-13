from dataclasses import dataclass

@dataclass
class ClickHouseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str