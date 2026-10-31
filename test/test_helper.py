import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.resolve()


def _resolve_riag_root(anchor: Path | None = None) -> Path:
    repo_root = (anchor or _REPO_ROOT).resolve()
    for candidate in (repo_root, *repo_root.parents):
        if (candidate / "dataset").is_dir():
            return candidate
        if candidate.name == "python_api" and candidate.parent.name == "tools":
            return candidate.parent.parent
        if (candidate / "riagraph" / "dataset").is_dir():
            return candidate / "riagraph"
    return repo_root


RIAG_ROOT_PATH = _resolve_riag_root()
DATASET_ROOT = RIAG_ROOT_PATH / "dataset"

if sys.platform == "win32":
    # \ in paths is not supported by riag's parser
    RIAG_ROOT = RIAG_ROOT_PATH.as_posix()
else:
    RIAG_ROOT = str(RIAG_ROOT_PATH)
