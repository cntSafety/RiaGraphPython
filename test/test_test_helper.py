from pathlib import Path

from riag_test_paths import _resolve_riag_root


def test_resolve_riag_root_handles_nested_ci_checkout() -> None:
    repo_root = Path(
        "/home/runner/work/riagraph-python/riagraph-python/riagraph/tools/python_api"
    )

    assert (
        _resolve_riag_root(repo_root)
        .as_posix()
        .endswith("/riagraph-python/riagraph-python/riagraph")
    )


def test_nested_ci_checkout_dataset_path_is_outside_python_api_tree() -> None:
    repo_root = Path(
        "/home/runner/work/riagraph-python/riagraph-python/riagraph/tools/python_api"
    )

    dataset_root = _resolve_riag_root(repo_root) / "dataset"
    assert dataset_root.as_posix().endswith(
        "/riagraph-python/riagraph-python/riagraph/dataset"
    )


def test_nested_ci_checkout_prefers_parent_riagraph_root_over_local_dataset_dir() -> (
    None
):
    repo_root = Path(
        "/home/runner/work/riagraph-python/riagraph-python/riagraph/tools/python_api"
    )

    resolved = _resolve_riag_root(repo_root)
    assert resolved.name == "riagraph"
    assert "/tools/python_api" not in resolved.as_posix()
