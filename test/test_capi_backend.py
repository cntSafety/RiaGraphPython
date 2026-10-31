from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
import riag as lb

if TYPE_CHECKING:
    from pathlib import Path


def test_capi_backend_basic_query() -> None:
    db = lb.Database(":memory:")
    conn = lb.Connection(db)

    result = conn.execute("RETURN 1 AS a;")
    assert result.get_next() == [1]

    conn.close()
    db.close()


def test_capi_backend_parameter_binding() -> None:
    db = lb.Database(":memory:")
    conn = lb.Connection(db)

    assert conn.execute("RETURN $x + 1 AS v;", {"x": 1}).get_next()[0] == 2
    assert conn.execute("RETURN $d AS v;", {"d": date(2024, 1, 2)}).get_next()[
        0
    ] == date(2024, 1, 2)
    assert conn.execute(
        "RETURN $ts AS v;", {"ts": datetime(2024, 1, 2, 3, 4, 5)}
    ).get_next()[0] == datetime(2024, 1, 2, 3, 4, 5)
    assert conn.execute("RETURN $v AS v;", {"v": {"a": 1, "b": [1, 2]}}).get_next()[
        0
    ] == {
        "a": 1,
        "b": [1, 2],
    }

    conn.close()
    db.close()


def test_capi_system_config_mirrors_the_c_struct() -> None:
    # riag_system_config travels by value. If the ctypes mirror is shorter than the C struct,
    # riag_default_system_config() writes past it and riag_database_init() reads past it,
    # so the trailing fields must come back with their C defaults.
    try:
        from riag import _riag_capi as capi
    except RuntimeError as e:
        pytest.skip(f"C API library not available: {e}")
    config = capi._LIB.riag_default_system_config()
    assert config.enable_default_hash_index is True
    assert config.physical_plan_pool_per_thread == 5


def test_capi_backend_exits_cleanly_next_to_pybind(build_dir: Path) -> None:
    # Both backends in one process means two copies of the engine. The library loaded second
    # has to bind its own symbols, or calls cross into the other copy: every C-API process
    # that ran a query (and with it imported the pybind module) crashed at exit.
    try:
        from riag import _riag_capi  # noqa: F401
    except RuntimeError as e:
        pytest.skip(f"C API library not available: {e}")
    code = dedent(f"""
        import sys
        sys.path.append(r"{build_dir!s}")
        import riag as lb
        from riag._backend import get_pybind_module

        db = lb.Database(":memory:")
        conn = lb.Connection(db)
        assert conn.execute("RETURN 1 + 1").get_next() == [2]
        get_pybind_module()
        assert conn.execute("UNWIND range(1, 3) AS x RETURN sum(x)").get_next() == [6]
    """)
    env = dict(os.environ, RIAG_PYTHON_BACKEND="capi")
    result = subprocess.run([sys.executable, "-c", code], env=env, check=False)
    assert result.returncode == 0
