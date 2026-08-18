import logging
from collections.abc import Iterator
from typing import Any

import requests

from ingestion_engine.config.api_config import APIConfig
from ingestion_engine.schema.table import TableConfig

from .base import BaseConnector

logger = logging.getLogger(__name__)


class APIConnector(BaseConnector):
    """Connector extracting records from a REST API endpoint.

    The endpoint is expected to answer with a JSON array of records.
    """

    def __init__(self, config: APIConfig) -> None:
        self.config = config

    def extract(self, table: TableConfig) -> Iterator[dict[str, Any]]:
        """Extract records from the configured API endpoint.

        Args:
            table: Configuration of the table being ingested. Accepted to
                honour the connector interface, but not used to build the
                request: the endpoint is fully defined by APIConfig.

        Yields:
            dict: Each record returned by the API.

        Raises:
            requests.exceptions.MissingSchema: If the configured URL has no
                valid scheme.
            requests.exceptions.Timeout: If the request exceeds the timeout.
            RuntimeError: If the request fails for another reason.
        """

        logger.info(
            "Extraction started, requesting data from %s",
            self.config.url,
        )

        try:
            response = requests.get(
                self.config.url,
                headers=self.config.headers,
                params=self.config.params,
                timeout=self.config.timeout,
            )

            response.raise_for_status()

            logger.info(
                "Received response with status code = %d",
                response.status_code,
            )

            yield from response.json()

        except requests.exceptions.MissingSchema:
            logger.exception(
                "Invalid API URL: %s",
                self.config.url,
            )
            raise

        except requests.exceptions.Timeout:
            logger.exception(
                "Request to %s timed out (connect=%.1fs, read=%.1fs)",
                self.config.url,
                self.config.connect_timeout,
                self.config.read_timeout,
            )
            raise

        except requests.exceptions.RequestException as e:
            logger.exception(
                "Failed to retrieve data from %s",
                self.config.url,
            )
            raise RuntimeError(f"Failed to retrieve data from {self.config.url}") from e
