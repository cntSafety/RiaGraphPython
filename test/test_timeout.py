from __future__ import annotations

import time

import pytest
from type_aliases import ConnDB


def test_timeout(conn_db_readonly: ConnDB) -> None:
    conn, _ = conn_db_readonly
    conn.set_query_timeout(1000)
    with pytest.raises(RuntimeError, match=r"Interrupted."):
        conn.execute(
            "UNWIND RANGE(1,100000) AS x UNWIND RANGE(1, 100000) AS y RETURN COUNT(x + y);"
        )


# Runs for a few seconds without a timeout (the two UNWINDs multiply the range).
SLOW_QUERY = "WITH range(1, 20000) AS r UNWIND r AS x UNWIND r AS y RETURN sum(x * y)"
# Needs a few milliseconds up to a few tenths of a second, whatever the machine.
SHORT_QUERY = "WITH range(1, 4000) AS r UNWIND r AS x UNWIND r AS y RETURN sum(x * y)"


def test_timeout_does_not_interrupt_a_query_within_the_limit(
    conn_db_readonly: ConnDB,
) -> None:
    # The C-API backend once armed its own timer at min(timeout, 10 ms), which
    # interrupted every query running longer than 10 ms as soon as any timeout was set.
    conn, _ = conn_db_readonly
    expected = conn.execute(SHORT_QUERY).get_next()
    conn.set_query_timeout(60000)
    start = time.monotonic()
    assert conn.execute(SHORT_QUERY).get_next() == expected
    # Guards the premise: the query must outlast the 10 ms of the old timer.
    assert time.monotonic() - start > 0.01


def test_timeout_interrupts_a_query_after_the_limit(conn_db_readonly: ConnDB) -> None:
    conn, _ = conn_db_readonly
    conn.set_query_timeout(300)
    start = time.monotonic()
    with pytest.raises(RuntimeError, match=r"Interrupted."):
        conn.execute(SLOW_QUERY)
    elapsed = time.monotonic() - start
    assert elapsed >= 0.2
    assert elapsed < 30


def test_timeout_does_not_interrupt_short_nested_unwind_range(
    conn_db_readonly: ConnDB,
) -> None:
    # The C-API backend once raised a fabricated "Interrupted." for any query with
    # two UNWIND RANGE( clauses while a timeout was set.
    conn, _ = conn_db_readonly
    conn.set_query_timeout(60000)
    result = conn.execute(
        "UNWIND RANGE(1, 10) AS x UNWIND RANGE(1, 10) AS y RETURN COUNT(x + y);"
    )
    assert result.get_next() == [100]
