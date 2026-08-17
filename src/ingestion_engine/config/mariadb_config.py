from dataclasses import dataclass

@dataclass(slots=True)
class MariaDBConfig:
    """Connection settings of the source MariaDB server.

    Attributes:
        host: Hostname or address of the MariaDB server.
        user: User the connection authenticates as.
        password: Password of the user.
        database: Database the records are extracted from.
    """

    host: str
    user: str
    password: str
    database: str