from collections.abc import Iterable, Iterator
import logging

logger = logging.getLogger(__name__)

def batcher(
    rows: Iterable[tuple],
    batch_size: int,
) -> Iterator[list[tuple]]:
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