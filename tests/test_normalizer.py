"""Tests for DictNormalizer, which reshapes source records into rows."""

from typing import Any

import pytest

from ingestion_engine import Column, DictNormalizer, TableConfig


def normalize(
    table: TableConfig, records: list[dict[str, Any]]
) -> list[tuple[Any, ...]]:
    return list(DictNormalizer().normalize(iter(records), table))


def test_values_follow_the_declared_column_order():
    """The loader inserts positionally, so column order defines row order."""

    table = TableConfig(
        name="t",
        columns=[
            Column("second", "String", "b"),
            Column("first", "String", "a"),
        ],
        order_by="second",
        source="test",
    )

    assert normalize(table, [{"a": "A", "b": "B"}]) == [("B", "A")]


def test_a_dotted_source_address_walks_nested_records(table):
    records = [{"id": 1, "meta": {"label": "first"}}]

    assert normalize(table, records) == [(1, "first")]


def test_deeply_nested_addresses_are_resolved():
    table = TableConfig(
        name="t",
        columns=[Column("lat", "String", "address.geo.lat")],
        order_by="lat",
        source="test",
    )

    records = [{"address": {"geo": {"lat": "-37.3"}}}]

    assert normalize(table, records) == [("-37.3",)]


def test_fields_outside_the_configuration_are_dropped(table):
    records = [{"id": 1, "meta": {"label": "x"}, "ignored": "gone"}]

    assert normalize(table, records) == [(1, "x")]


def test_every_record_becomes_one_row(table):
    records = [{"id": i, "meta": {"label": str(i)}} for i in range(4)]

    assert normalize(table, records) == [(0, "0"), (1, "1"), (2, "2"), (3, "3")]


def test_no_records_produce_no_rows(table):
    assert normalize(table, []) == []


def test_values_are_passed_through_without_conversion():
    """The normalizer reshapes records, it does not cast values.

    This is why a column type has to match what the source really returns.
    """

    table = TableConfig(
        name="t",
        columns=[Column("lat", "Float64", "lat")],
        order_by="lat",
        source="test",
    )

    rows = normalize(table, [{"lat": "-37.3"}])

    assert rows == [("-37.3",)]
    assert isinstance(rows[0][0], str)


def test_a_missing_field_raises_key_error(table):
    with pytest.raises(KeyError):
        normalize(table, [{"id": 1}])


def test_a_missing_intermediate_key_raises_key_error(table):
    with pytest.raises(KeyError):
        normalize(table, [{"id": 1, "meta": {}}])


def test_traversing_into_a_non_mapping_raises_type_error(table):
    with pytest.raises(TypeError):
        normalize(table, [{"id": 1, "meta": 5}])


def test_records_are_normalized_one_at_a_time(table, counting_source):
    """Normalization must stay lazy, or the whole source is held in memory."""

    source = counting_source([{"id": i, "meta": {"label": "x"}} for i in range(50)])
    rows = DictNormalizer().normalize(iter(source), table)

    next(rows)

    assert source.consumed == 1
