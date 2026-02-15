"""Built-in gmpp components (parser wrappers).

Each import triggers @register_component registration. All built-in
components use lazy imports for their third-party dependencies (inside
process()), so these imports should always succeed. The ImportError
guard is a safety net for future components that might import at
module level.
"""

import importlib
import warnings

_COMPONENT_MODULES = [
    "gmpp.components.trafilatura",
    "gmpp.components.readability",
    "gmpp.components.justext",
    "gmpp.components.newspaper",
    "gmpp.components.inscriptis",
]

for _mod in _COMPONENT_MODULES:
    try:
        importlib.import_module(_mod)
    except ImportError as exc:
        warnings.warn(
            f"Failed to import {_mod}: {exc}. "
            f"The component will not be available.",
            stacklevel=1,
        )
