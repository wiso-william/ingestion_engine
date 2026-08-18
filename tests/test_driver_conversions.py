"""Characterisation tests for the conversions the ClickHouse driver performs.

These do not test this project's code. They pin down the behaviour the README
documents under Limitations, which belongs to clickhouse-connect: which
mismatches between a declared column type and a source value are converted,
which are refused, and how the outcome depends on the order of the rows.

They exist because that behaviour was once documented wrong, from a measurement
taken at the wrong layer. If a release of the driver changes any of it, these
tests fail and the README has to be corrected along with them. Being brittle is
the point: the exception classes are asserted precisely, so a change in how a
value is refused is visible rather than silent.

The driver converts on the client while serialising a column, so no server is
needed here: an InsertContext is built by hand and a single column is serialised
through it, exactly as an insert would do.
"""

import struct
from datetime import datetime
from typing import Any

import pytest
from clickhouse_connect.datatypes.registry import get_from_name
from clickhouse_connect.driver.exceptions import DataError
from clickhouse_connect.driver.insert import InsertContext


def serialise(clickhouse_type: str, values: list[Any]) -> bytearray:
    """Serialise one column the way an insert would.

    Args:
        clickhouse_type: Declared type of the destination column.
        values: Source values for that column.

    Returns:
        bytearray: The column in ClickHouse's native format.

    Raises:
        Exception: Whatever the driver raises when a value does not fit.
    """

    column_type = get_from_name(clickhouse_type)
    context = InsertContext(
        "probe", ["v"], [column_type], data=[[value] for value in values]
    )
    context.column_name = "v"

    destination = bytearray()
    column_type.write_column(list(values), destination, context)

    return destination


def stored(clickhouse_type: str, value: Any, struct_format: str) -> Any:
    """Return a single value as the driver would store it.

    Args:
        clickhouse_type: Declared type of the destination column.
        value: Source value.
        struct_format: struct code of the destination type, used to read the
            serialised bytes back.

    Returns:
        The value after whatever conversion the driver applied.
    """

    return struct.unpack("<" + struct_format, serialise(clickhouse_type, [value]))[0]


class TestConverted:
    """Mismatches the driver resolves instead of refusing."""

    @pytest.mark.parametrize(
        ("clickhouse_type", "value", "struct_format", "expected"),
        [
            ("Float64", "-37.3159", "d", -37.3159),
            ("Float64", "0", "d", 0.0),
            ("UInt64", "42", "Q", 42),
            ("UInt8", "3", "B", 3),
            ("Int32", "-7", "i", -7),
        ],
        ids=["float-from-text", "zero-from-text", "uint64", "uint8", "negative-int32"],
    )
    def test_a_numeric_string_is_parsed_into_the_declared_numeric_type(
        self, clickhouse_type, value, struct_format, expected
    ):
        """This is what lets users.py declare the API's geo.lat as Float64."""

        assert stored(clickhouse_type, value, struct_format) == expected

    def test_an_integer_widens_into_a_float_column(self):
        assert stored("Float64", 3, "d") == 3.0

    def test_a_float_is_truncated_into_an_integer_column(self):
        """Information is lost here, silently, and the driver allows it.

        Documented rather than guarded: deciding what a value should become is
        transformation, which this framework leaves to staging.
        """

        assert stored("UInt8", 3.7, "B") == 3

    def test_a_numeric_string_is_parsed_into_a_decimal_column(self):
        """Decimal has no struct format, so only acceptance is checked here."""

        assert serialise("Decimal(10, 2)", ["12.34"])

    @pytest.mark.parametrize(
        "value",
        ["2024-01-15 10:00:00", "2024-01-15T10:00:00"],
        ids=["space-separated", "iso-t"],
    )
    def test_an_iso_string_is_parsed_into_a_datetime64_column(self, value):
        """DateTime64 parses ISO strings, unlike Date and DateTime.

        The result is indistinguishable from passing a datetime object, which is
        what the comparison below checks.
        """

        assert serialise("DateTime64(3)", [value]) == serialise(
            "DateTime64(3)", [datetime(2024, 1, 15, 10, 0, 0)]
        )

    def test_none_is_accepted_by_a_nullable_column(self):
        assert serialise("Nullable(String)", [None]) is not None


class TestRefused:
    """Mismatches the driver refuses, so a pipeline fails instead of guessing.

    Every exception here reaches `run`, which wraps it into a RuntimeError
    naming the table, so any of them stops the ingestion.
    """

    def test_a_string_that_is_not_an_integer(self):
        with pytest.raises(ValueError, match="invalid literal for int"):
            serialise("UInt8", ["3.7"])

    @pytest.mark.parametrize(
        ("clickhouse_type", "value"),
        [("Int8", 130), ("Int8", -129), ("UInt8", 256), ("UInt8", -1)],
        ids=["int8-above", "int8-below", "uint8-above", "uint8-negative"],
    )
    def test_a_value_outside_the_range_of_the_declared_type(
        self, clickhouse_type, value
    ):
        with pytest.raises(DataError, match="Unable to create native array"):
            serialise(clickhouse_type, [value])

    def test_a_string_for_a_date_column(self):
        with pytest.raises(TypeError, match="unsupported operand type"):
            serialise("Date", ["2024-01-15"])

    def test_a_string_for_a_datetime_column(self):
        with pytest.raises(AttributeError, match="has no attribute 'timestamp'"):
            serialise("DateTime", ["2024-01-15 10:00:00"])

    def test_a_string_that_is_not_a_date_for_a_datetime64_column(self):
        """DateTime64 parses ISO strings, but only those."""

        with pytest.raises(ValueError, match="Invalid isoformat string"):
            serialise("DateTime64(3)", ["not a date"])

    @pytest.mark.parametrize("value", [123, 1.5], ids=["int", "float"])
    def test_a_non_string_for_a_string_column(self, value):
        with pytest.raises(AttributeError, match="has no attribute 'encode'"):
            serialise("String", [value])

    def test_none_for_a_column_that_is_not_nullable(self):
        with pytest.raises(DataError, match="Invalid None value"):
            serialise("String", [None])


class TestRowOrder:
    """The driver reads a whole column as the type of its first value.

    This is the surprising part, and the reason the README warns about it: the
    same values load or fail depending on which row comes first.
    """

    def test_a_text_first_column_accepts_the_numbers_that_follow(self):
        assert serialise("Float64", ["1.5", 2.5])

    def test_a_number_first_column_refuses_the_text_that_follows(self):
        with pytest.raises(DataError, match="Unable to create native array"):
            serialise("Float64", [1.5, "2.5"])
