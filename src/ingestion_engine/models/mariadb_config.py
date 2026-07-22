from dataclasses import dataclass

@dataclass(slots=True)
class MariaDBConfig:
    host: str
    user: str
    password: str
    database: str