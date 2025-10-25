"""
Proxy package initializer for `cms.djangoapps.contentstore.utils`.

Historically this codebase used a single module `utils.py` at the
`cms/djangoapps/contentstore` level. At some point a `utils/` package
was created accidentally which caused imports like

	from cms.djangoapps.contentstore.utils import reverse_usage_url

to resolve to this package instead of the original `utils.py` file.

To remain compatible we dynamically load the original `utils.py`
file (located one level up) and re-export the attributes commonly
imported from it. This avoids changing many import sites across the
codebase while keeping the helper code in `utils.py`.

This file intentionally uses importlib to load the sibling module by
file path and injects its public attributes into this package's
namespace.
"""

from __future__ import annotations

import importlib.util
import importlib.machinery
import os
import sys
from types import ModuleType

# Path to the sibling utils.py file (one level up from this package)
_THIS_DIR = os.path.dirname(__file__)
_SIBLING_UTILS_PATH = os.path.abspath(os.path.join(_THIS_DIR, '..', 'utils.py'))


def _load_sibling_utils_module(path: str) -> ModuleType:
	"""Load a module from a file path and return the module object.

	We avoid using the regular import system here because the package
	name `cms.djangoapps.contentstore.utils` is already taken by this
	package. Loading by file path lets us access the original module
	implementation contained in `utils.py`.
	
	The module must be loaded with proper package context so that relative
	imports within utils.py work correctly.
	"""
	# Use a unique module name that indicates its parent package for relative imports
	module_name = "cms.djangoapps.contentstore._utils_compat"
	spec = importlib.util.spec_from_file_location(module_name, path)
	if spec is None or spec.loader is None:
		raise ImportError(f"Could not load utils module from path: {path}")
	module = importlib.util.module_from_spec(spec)
	# Set __package__ so relative imports work
	module.__package__ = "cms.djangoapps.contentstore"
	# Register in sys.modules before execution so imports can find it
	sys.modules[module_name] = module
	try:
		# Execute the module in its properly configured namespace
		spec.loader.exec_module(module)  # type: ignore[attr-defined]
	except Exception:
		# Clean up on failure
		sys.modules.pop(module_name, None)
		raise
	return module


_sibling = None
_load_error = None

try:
	_sibling = _load_sibling_utils_module(_SIBLING_UTILS_PATH)
except Exception as exc:
	# If for some reason the sibling utils.py cannot be loaded, expose a
	# clear ImportError when callers attempt to access missing attributes.
	_sibling = None
	_load_error = exc


def __getattr__(name: str):
	"""Delegate attribute lookups to the loaded sibling utils module."""
	if _sibling is None:
		error_msg = f"The legacy cms.djangoapps.contentstore.utils module could not be loaded from {_SIBLING_UTILS_PATH}"
		if _load_error is not None:
			error_msg += f"\nOriginal error: {type(_load_error).__name__}: {_load_error}"
		raise ImportError(error_msg)
	try:
		return getattr(_sibling, name)
	except AttributeError as exc:
		raise AttributeError(f"module 'cms.djangoapps.contentstore.utils' has no attribute '{name}'") from exc


def __dir__() -> list[str]:
	if _sibling is None:
		return []
	return sorted(set(dir(_sibling)))

