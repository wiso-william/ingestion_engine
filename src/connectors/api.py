import requests
from collections.abc import Iterator

from .base import BaseConnector
from src.models.api_config import APIConfig

class APIConnector(BaseConnector):

    def __init__(self, config: APIConfig):
        self.config = config

    def extract(self) -> Iterator[dict]:

        response = requests.get(
            self.config.url,
            headers=self.config.headers,
            params=self.config.params,
        )

        response.raise_for_status()

        for record in response.json():
            yield record