"""Component base class — one processing step in a pipeline."""

import inspect
from abc import ABC, abstractmethod
from typing import Any

from gmpp.document import Document
from gmpp.registry import create_component


class Component(ABC):
    """Abstract base class for all pipeline components.

    Subclasses must:
    - Set the ``output_field`` class attribute.
    - Implement ``process(doc)``.
    """

    output_field: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "__abstractmethods__", None) and not hasattr(cls, "output_field"):
            raise TypeError(
                f"Component subclass {cls.__name__!r} must define "
                f"an 'output_field' class attribute."
            )

    # -- identity -------------------------------------------------------------

    @property
    def name(self) -> str:
        """Human-readable name derived from the class name."""
        return type(self).__name__

    # -- core interface -------------------------------------------------------

    @abstractmethod
    def process(self, doc: Document) -> Document:
        """Process a single document. Must write to ``doc.content[self.output_field]``."""
        ...

    def setup(self, corpus: list[Document]) -> None:
        """Optional hook called once before processing a corpus.

        Override for corpus-aware components (e.g., template induction).
        """

    # -- param introspection (scikit-learn style) -----------------------------

    def get_params(self) -> dict[str, Any]:
        """Return a dict of constructor parameters and their current values."""
        sig = inspect.signature(self.__init__)  # type: ignore[misc]
        params: dict[str, Any] = {}
        for name, _param in sig.parameters.items():
            if name == "self":
                continue
            if _param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            params[name] = getattr(self, name, _param.default)
        return params

    def set_params(self, **params: Any) -> None:
        """Set attributes corresponding to constructor parameters."""
        for key, value in params.items():
            setattr(self, key, value)

    # -- serialization --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict suitable for JSON config files."""
        registered_name = getattr(type(self), "_registered_name", self.name)
        return {"name": registered_name, "params": self.get_params()}

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "Component":
        """Reconstruct a Component from a config dict via the registry."""
        return create_component(config["name"], **config.get("params", {}))

    # -- display --------------------------------------------------------------

    def __repr__(self) -> str:
        params = self.get_params()
        param_str = ", ".join(f"{k}={v!r}" for k, v in params.items())
        return f"{self.name}({param_str})"
