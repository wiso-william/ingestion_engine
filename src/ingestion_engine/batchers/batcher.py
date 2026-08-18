import logging
from collections.abc import Iterable, Iterator
from typing import Any

logger = logging.getLogger(__name__)


def batcher(
    rows: Iterable[tuple[Any, ...]],
    batch_size: int,
) -> Iterator[list[tuple[Any, ...]]]:
    """Group rows into batches of fixed size.

    Rows are consumed lazily, so only one batch at a time is kept in memory.

    Args:
        rows: Normalized rows to group.
        batch_size: Maximum number of rows per batch.

    Yields:
        list[tuple]: Batches of rows. Only the last batch can be smaller than
            batch_size.
    """

    batch: list[tuple[Any, ...]] = []

    logger.debug("Starting batcher with batch size %d", batch_size)

    for row in rows:
        batch.append(row)

        if len(batch) == batch_size:
            logger.debug("Yielding batch of size %d", batch_size)
            yield batch
            batch = []

    if batch:
        logger.debug("Yielding final batch of size %d", len(batch))
        yield batch
