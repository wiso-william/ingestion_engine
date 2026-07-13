from collections.abc import Iterable, Iterator

def batcher(
    rows: Iterable[tuple],
    batch_size: int,
) -> Iterator[list[tuple]]:
    batch: list[tuple] = []

    for row in rows:
        batch.append(row)

        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch