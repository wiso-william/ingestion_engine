from dataclasses import dataclass

@dataclass
class APIConfig:
    """Settings of the HTTP request used to extract records from an API.

    Attributes:
        url: URL of the endpoint returning the records.
        headers: HTTP headers sent with the request.
        params: Query string parameters sent with the request.
    """

    url: str
    headers: dict[str, str]
    params: dict[str, str]