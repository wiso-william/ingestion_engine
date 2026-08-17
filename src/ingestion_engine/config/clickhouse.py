from dataclasses import dataclass

@dataclass
class ClickHouseConfig:
    """Connection settings of the destination ClickHouse server.

    Attributes:
        host: Hostname or address of the ClickHouse server.
        port: Port the server listens on.
        user: User the connection authenticates as.
        password: Password of the user.
        database: Database the records are loaded into.
    """

    host: str
    port: int
    user: str
    password: str
    database: str