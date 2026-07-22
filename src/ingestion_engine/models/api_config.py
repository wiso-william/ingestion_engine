from dataclasses import dataclass

@dataclass
class APIConfig:
    url: str
    headers: dict[str, str]
    params: dict[str, str]