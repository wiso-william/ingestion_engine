"""Tests for the batcher, which groups normalized rows before loading."""

from ingestion_engine.batchers.batcher import batcher


def rows(count: int) -> list[tuple]:
    return [(i,) for i in range(count)]


def test_splits_into_batches_of_the_requested_size():
    assert list(batcher(rows(6), 2)) == [
        [(0,), (1,)],
        [(2,), (3,)],
        [(4,), (5,)],
    ]


def test_last_batch_holds_the_remainder():
    batches = list(batcher(rows(7), 3))

    assert [len(batch) for batch in batches] == [3, 3, 1]


def test_no_rows_yields_no_batches():
    assert list(batcher([], 10)) == []


def test_fewer_rows_than_the_batch_size_yield_a_single_batch():
    assert list(batcher(rows(2), 10)) == [[(0,), (1,)]]


def test_row_count_and_order_are_preserved():
    batches = list(batcher(rows(10), 3))
    flattened = [row for batch in batches for row in batch]

    assert flattened == rows(10)


def test_reads_only_what_the_current_batch_needs():
    """The source must not be drained upfront, or memory use grows with it."""

    consumed = 0

    def source():
        nonlocal consumed
        for row in rows(100):
            consumed += 1
            yield row

    batches = batcher(source(), 10)

    next(batches)
    assert consumed == 10

    next(batches)
    assert consumed == 20


def test_a_batch_size_of_zero_would_never_flush():
    """Guards the contract: batch_size must be positive.

    With zero the size check never matches, so every row accumulates into a
    single batch instead of being flushed. The batcher does not validate its
    input, so this documents the behaviour rather than endorsing it.
    """

    batches = list(batcher(rows(5), 0))

    assert batches == [rows(5)]
