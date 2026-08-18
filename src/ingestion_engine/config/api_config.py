from dataclasses import dataclass


DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 30.0


@dataclass
class APIConfig:
    """Settings of the HTTP request used to extract records from an API.

    Attributes:
        url: URL of the endpoint returning the records.
        headers: HTTP headers sent with the request.
        params: Query string parameters sent with the request.
        connect_timeout: Seconds to wait for the connection to be established
            before giving up.
        read_timeout: Seconds to wait between two bytes sent by the server
            before giving up. Without it a stalled endpoint would hang the
            pipeline forever.
    """

    url: str
    headers: dict[str, str]
    params: dict[str, str]
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT
    read_timeout: float = DEFAULT_READ_TIMEOUT

    @property
    def timeout(self) -> tuple[float, float]:
        """Timeout pair in the form expected by requests.

        Returns:
            tuple[float, float]: The connect and read timeouts, in seconds.
        """

        return (self.connect_timeout, self.read_timeout)
