from dataclasses import dataclass


DEFAULT_PORT = 3306


@dataclass(slots=True)
class MariaDBConfig:
    """Connection settings of the source MariaDB server.

    Attributes:
        host: Hostname or address of the MariaDB server.
        user: User the connection authenticates as.
        password: Password of the user.
        database: Database the records are extracted from.
        port: Port the server listens on.
    """

    host: str
    user: str
    password: str
    database: str
    port: int = DEFAULT_PORT
