from __future__ import annotations

import os
import sys
from importlib import import_module
from typing import Any

_CAPI_MODULE: Any | None = None
_PYBIND_MODULE: Any | None = None
_PYBIND_IMPORT_ATTEMPTED = False


def _import_pybind_module() -> Any:
    if sys.platform != "linux":
        return import_module("._riag", __package__)

    original_dlopen_flags = sys.getdlopenflags()
    try:
        # Keep pybind's symbols visible to any transitive native extensions
        # without affecting the process-wide import path for the C-API backend.
        flags = os.RTLD_GLOBAL | os.RTLD_LAZY
        if f"{__package__}._riag_capi" in sys.modules:
            # The C-API backend's library, already loaded and globally visible, holds a second
            # copy of the engine; bind this module's symbols to itself so the two never mix.
            # Only the copy loaded second needs it; sanitizer runtimes reject the flag.
            flags |= getattr(os, "RTLD_DEEPBIND", 0)
        sys.setdlopenflags(flags)
        return import_module("._riag", __package__)
    finally:
        sys.setdlopenflags(original_dlopen_flags)


def get_capi_module() -> Any:
    global _CAPI_MODULE
    if _CAPI_MODULE is None:
        _CAPI_MODULE = import_module("._riag_capi", __package__)
    return _CAPI_MODULE


def get_pybind_module() -> Any | None:
    global _PYBIND_MODULE, _PYBIND_IMPORT_ATTEMPTED
    if _PYBIND_IMPORT_ATTEMPTED:
        return _PYBIND_MODULE
    _PYBIND_IMPORT_ATTEMPTED = True
    try:
        _PYBIND_MODULE = _import_pybind_module()
    except ImportError:
        _PYBIND_MODULE = None
    return _PYBIND_MODULE
