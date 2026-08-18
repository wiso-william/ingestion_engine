import logging
from collections.abc import Iterable, Iterator

logger = logging.getLogger(__name__)


def batcher(
    rows: Iterable[tuple],
    batch_size: int,
) -> Iterator[list[tuple]]:
    """Group rows into batches of fixed size.

    Rows are consumed lazily, so only one batch at a time is kept in memory.

    Args:
        rows: Normalized rows to group.
        batch_size: Maximum number of rows per batch.

    Yields:
        list[tuple]: Batches of rows. Only the last batch can be smaller than
            batch_size.
    """

    batch: list[tuple] = []

    logger.debug(f"Starting batcher with batch size {batch_size}")

    for row in rows:
        batch.append(row)

        if len(batch) == batch_size:
            logger.debug(f"Yielding batch of size {batch_size}")
            yield batch
            batch = []

    if batch:
        logger.debug(f"Yielding final batch of size {len(batch)}")
        yield batch
