# Python APIs

## Build

### C-API backend (default)

```bash
make sync
```

This downloads the latest shared `libriag` binary (via upstream
`download-libriag.sh`) and syncs the project with dev dependencies.
The Python package is installed directly from `src_py/`, so the standalone
workflow no longer depends on `./build/riag`.

In order to run tests you'll need to pull data first with:

```bash
git submodule update --init --recursive
```

Then run tests with:

```bash
uv run pytest -n $(nproc)
```

### Pybind backend from inverted layout

If your checkout layout is:

- `riagraph-python/` (this repo)
- `../riagraph/` (main RiaGraph repo as a sibling checkout)

then build the pybind extension through the RiaGraph top-level build with:

```bash
make build-pybind-subdir
```

This uses `RIAG_SOURCE_DIR` (default: `../riagraph`) to configure this repo's
CMake build against the RiaGraph source checkout and writes `_riag*` into
`./build/riag`.

Run tests against that pybind build with:

```bash
make test-pybind-subdir
```

Override the source tree location when needed:

```bash
make build-pybind-subdir RIAG_SOURCE_DIR=/path/to/riagraph
```

## Formatting

Code is formatted with **black** and linted with **ruff**:

```bash
make lint        # black + ruff check + mypy
make format      # black only
make check       # ruff check only (verbose)
```

We also have a pre-commit hook for formatting and linting:

```bash
uv run --no-sync pre-commit install
```
