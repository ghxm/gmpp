"""Built-in gmpp components (parser wrappers)."""

# Each import triggers @register_component registration.
# ImportErrors are silenced -- components are only available
# if the corresponding optional dependency is installed.

import importlib

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
    except ImportError:
        pass
