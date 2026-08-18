"""Tests for run(), the function wiring the four stages together.

The normalizer and the batcher are the real ones here: what is faked is only
what talks to the outside world, so these tests cover the actual interaction
between the stages.
"""

import pytest

from ingestion_engine import BaseConnector, BaseLoader, DictNormalizer, run


class RecordingLoader(BaseLoader):
    """A loader that records the calls it receives instead of writing."""

    def __init__(self, probe=None, create_error=None, load_error=None):
        self.probe = probe
        self.create_error = create_error
        self.load_error = load_error
        self.created: list[str] = []
        self.batches: list[list[tuple]] = []
        self.records_read_at_create = None

    def create_table(self, table) -> None:
        if self.probe is not None:
            self.records_read_at_create = self.probe.consumed

        if self.create_error is not None:
            raise self.create_error

        self.created.append(table.name)

    def load(self, table, rows) -> None:
        if self.load_error is not None:
            raise self.load_error

        self.batches.append(list(rows))

    @property
    def rows(self) -> list[tuple]:
        return [row for batch in self.batches for row in batch]


class SourceConnector(BaseConnector):
    def __init__(self, source):
        self.source = source

    def extract(self, table):
        return iter(self.source)


def build_records(count: int) -> list[dict]:
    return [{"id": i, "meta": {"label": str(i)}} for i in range(count)]


class TestOrchestration:
    def test_the_table_is_created_before_the_source_is_read(
        self, table, counting_source
    ):
        """Extraction is lazy, so nothing is pulled until the batches are consumed."""

        source = counting_source(build_records(10))
        loader = RecordingLoader(probe=source)

        run(SourceConnector(source), DictNormalizer(), loader, table, batch_size=5)

        assert loader.records_read_at_create == 0

    def test_the_destination_table_is_created_once(self, table):
        loader = RecordingLoader()

        run(
            SourceConnector(build_records(10)),
            DictNormalizer(),
            loader,
            table,
            batch_size=2,
        )

        assert loader.created == ["events"]

    def test_rows_are_delivered_in_batches_of_the_requested_size(self, table):
        loader = RecordingLoader()

        run(
            SourceConnector(build_records(10)),
            DictNormalizer(),
            loader,
            table,
            batch_size=4,
        )

        assert [len(batch) for batch in loader.batches] == [4, 4, 2]

    def test_every_record_reaches_the_loader_normalized(self, table):
        loader = RecordingLoader()

        run(
            SourceConnector(build_records(3)),
            DictNormalizer(),
            loader,
            table,
            batch_size=2,
        )

        assert loader.rows == [(0, "0"), (1, "1"), (2, "2")]

    def test_an_empty_source_still_creates_the_table(self, table):
        """A full refresh of an empty source has to empty the destination."""

        loader = RecordingLoader()

        run(SourceConnector([]), DictNormalizer(), loader, table, batch_size=10)

        assert loader.created == ["events"]
        assert loader.batches == []

    def test_a_batch_size_is_not_required(self, table):
        loader = RecordingLoader()

        run(SourceConnector(build_records(5)), DictNormalizer(), loader, table)

        assert loader.rows == [(i, str(i)) for i in range(5)]


class TestFailures:
    def test_a_source_failure_is_reported_against_the_table(self, table):
        class FailingConnector(BaseConnector):
            def extract(self, table):
                raise ConnectionError("source unreachable")
                yield

        with pytest.raises(RuntimeError, match="failed for table events"):
            run(FailingConnector(), DictNormalizer(), RecordingLoader(), table)

    def test_a_create_table_failure_is_reported(self, table):
        loader = RecordingLoader(create_error=ValueError("bad ddl"))

        with pytest.raises(RuntimeError, match="failed for table events"):
            run(SourceConnector(build_records(1)), DictNormalizer(), loader, table)

    def test_a_load_failure_is_reported(self, table):
        loader = RecordingLoader(load_error=OSError("insert failed"))

        with pytest.raises(RuntimeError, match="failed for table events"):
            run(SourceConnector(build_records(1)), DictNormalizer(), loader, table)

    def test_a_record_missing_a_configured_field_is_reported(self, table):
        """Normalization failures must not escape as a bare KeyError."""

        with pytest.raises(RuntimeError, match="failed for table events"):
            run(
                SourceConnector([{"id": 1}]),
                DictNormalizer(),
                RecordingLoader(),
                table,
            )

    def test_the_original_failure_is_kept_as_the_cause(self, table):
        original = OSError("insert failed")
        loader = RecordingLoader(load_error=original)

        with pytest.raises(RuntimeError) as error:
            run(SourceConnector(build_records(1)), DictNormalizer(), loader, table)

        assert error.value.__cause__ is original
