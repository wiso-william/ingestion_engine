import logging
from collections.abc import Iterator
import requests

from .base import BaseConnector
from ingestion_engine.config.api_config import APIConfig


logger = logging.getLogger(__name__)


class APIConnector(BaseConnector):

    def __init__(self, config: APIConfig):
        self.config = config

    def extract(self) -> Iterator[dict]:

        logger.info("Extraction started, requesting data from %s", self.config.url)

        try:

            response = requests.get(
                self.config.url,
                headers=self.config.headers,
                params=self.config.params,
            )

            response.raise_for_status()

            logger.info("Received response with status code = %d", response.status_code)

            for record in response.json():
                yield record

        except requests.RequestException as e:
            logger.exception("Failed to retrieve data from %s", self.config.url)
            raise RuntimeError(f"Failed to retrieve data from {self.config.url}") from e    