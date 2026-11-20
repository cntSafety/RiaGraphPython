from __future__ import annotations

import datetime

import pytest
import riag as lb

# The engine's DATE and TIMESTAMP types reach far beyond Python's datetime range
# (years 1..9999). Fetching such a value used to take the interpreter down with
# SIGSEGV (the pybind backend wrapped a NULL PyObject); it must raise instead,
# on both backends, and name the value. The engine side is fine: the same
# expression cast to STRING prints the full value.

OUT_OF_RANGE = [
    # DATE above, below and just past either end of the range.
    "RETURN date('10000-01-01')",
    "RETURN date('0001-01-01') - 400",
    "RETURN date('0001-01-01') - 1",
    # TIMESTAMP and every TIMESTAMP_* variant.
    "RETURN timestamp('10000-01-01 00:00:00')",
    "RETURN timestamp('0001-01-01 00:00:00') - interval('1 microsecond')",
    "RETURN cast(cast('290000-01-01' AS TIMESTAMP) AS TIMESTAMP_TZ)",
    "RETURN cast(cast('10000-01-01 00:00:00' AS TIMESTAMP) AS TIMESTAMP_MS)",
    "RETURN cast(cast('10000-01-01 00:00:00' AS TIMESTAMP) AS TIMESTAMP_SEC)",
    # Nested in containers: the conversion recurses into them.
    "RETURN [date('10000-01-01')]",
    "RETURN {d: date('10000-01-01')}",
]

# The boundary values that must keep converting.
IN_RANGE = [
    ("RETURN date('0001-01-01')", datetime.date(1, 1, 1)),
    ("RETURN date('9999-12-31')", datetime.date(9999, 12, 31)),
    (
        "RETURN timestamp('0001-01-01 00:00:00')",
        datetime.datetime(1, 1, 1, 0, 0, 0),
    ),
    (
        "RETURN timestamp('9999-12-31 23:59:59.999999')",
        datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
    ),
    (
        "RETURN cast(timestamp('9999-12-31 23:59:59') AS TIMESTAMP_TZ)",
        datetime.datetime(9999, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc),
    ),
    (
        "RETURN cast(timestamp('9999-12-31 23:59:59') AS TIMESTAMP_SEC)",
        datetime.datetime(9999, 12, 31, 23, 59, 59),
    ),
    (
        "RETURN cast(timestamp('9999-12-31 23:59:59') AS TIMESTAMP_MS)",
        datetime.datetime(9999, 12, 31, 23, 59, 59),
    ),
    (
        "RETURN cast(timestamp('1900-01-01 00:00:00.123456') AS TIMESTAMP_NS)",
        datetime.datetime(1900, 1, 1, 0, 0, 0, 123456),
    ),
    ("RETURN date('1969-12-31')", datetime.date(1969, 12, 31)),
    (
        "RETURN timestamp('1969-12-31 23:59:59.999999')",
        datetime.datetime(1969, 12, 31, 23, 59, 59, 999999),
    ),
]


@pytest.fixture
def conn():
    db = lb.Database(":memory:")
    connection = lb.Connection(db)
    yield connection
    connection.close()
    db.close()


@pytest.mark.parametrize("query", OUT_OF_RANGE)
def test_out_of_range_raises_instead_of_crashing(conn: lb.Connection, query: str):
    with pytest.raises(ValueError, match="outside the range supported by Python's"):
        conn.execute(query).get_all()


@pytest.mark.parametrize("query", OUT_OF_RANGE)
def test_out_of_range_raises_from_get_next(conn: lb.Connection, query: str):
    result = conn.execute(query)
    with pytest.raises(ValueError, match="outside the range supported by Python's"):
        result.get_next()


def test_out_of_range_error_names_the_value(conn: lb.Connection):
    with pytest.raises(ValueError, match=r"DATE value .*10000"):
        conn.execute("RETURN date('10000-01-01')").get_all()
    with pytest.raises(ValueError, match=r"TIMESTAMP value .*10000"):
        conn.execute("RETURN timestamp('10000-01-01 00:00:00')").get_all()


@pytest.mark.parametrize(("query", "expected"), IN_RANGE)
def test_in_range_boundaries_still_convert(
    conn: lb.Connection, query: str, expected: datetime.date
):
    assert conn.execute(query).get_all() == [[expected]]


def test_connection_survives_an_out_of_range_value(conn: lb.Connection):
    with pytest.raises(ValueError):
        conn.execute("RETURN date('10000-01-01')").get_all()
    assert conn.execute("RETURN 1").get_all() == [[1]]
    # The engine value is intact: only the Python conversion is refused.
    assert conn.execute("RETURN cast(date('10000-01-01') AS STRING)").get_all() == [
        ["10000-01-01"]
    ]


def test_interval_out_of_timedelta_range_raises(conn: lb.Connection):
    # Already an ordinary Python exception; pin it so it stays one.
    with pytest.raises(OverflowError):
        conn.execute("RETURN to_days(1000000000)").get_all()


def test_dataframe_keeps_dates_past_year_2262():
    # The DataFrame path has no datetime object to refuse: it fills an int64
    # microsecond buffer. A DATE used to be routed through nanoseconds, which
    # overflows int64 past the year 2262 and silently wrapped to a wrong date.
    np = pytest.importorskip("numpy")
    pytest.importorskip("pandas")
    db = lb.Database(":memory:")
    if not db._use_pybind_backend:
        # The C-API backend builds DataFrames through Arrow, which has its own
        # (clean, OverflowError) limit for these dates.
        db.close()
        pytest.skip("pybind DataFrame conversion only")
    conn = lb.Connection(db)
    df = conn.execute(
        "RETURN date('3000-06-15') AS d, date('10000-01-01') AS far"
    ).get_as_df()
    assert df["d"].iloc[0] == np.datetime64("3000-06-15", "us")
    assert df["far"].iloc[0] == np.datetime64("10000-01-01", "us")
