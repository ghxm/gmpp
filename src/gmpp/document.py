"""Document and StepRecord — the data containers that flow through pipelines."""

import types
from dataclasses import dataclass, field
from typing import Any, NamedTuple


_CONTENT_SENTINEL: dict = {}  # identity-checked in __post_init__


class StepRecord(NamedTuple):
    """Record of a single processing step applied to a Document."""

    component_name: str
    output_field: str
    timestamp: str
    duration_s: float
    params: dict[str, Any]


@dataclass
class Document:
    """Mutable data container that flows through the pipeline.

    Attributes:
        input: Frozen snapshot of the original data. Never modified by components.
        content: Mutable working state. Components read from and write to this.
        eval: Evaluation data — ground truth and computed scores.
        history: Ordered list of StepRecords tracking provenance.
    """

    input: types.MappingProxyType[str, Any]
    content: dict[str, Any] = field(default_factory=lambda: _CONTENT_SENTINEL)
    eval: dict[str, Any] = field(
        default_factory=lambda: {"ground_truth": None, "scores": None}
    )
    history: list[StepRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Accept a regular dict in __init__ and freeze it.
        if isinstance(self.input, dict):
            self.input = types.MappingProxyType(self.input)

        # Initialize content as a mutable copy of input if not explicitly
        # provided. We use an identity check against the default_factory
        # sentinel rather than truthiness, so that content={} is preserved.
        if self.content is _CONTENT_SENTINEL:
            self.content = dict(self.input)

    # -- pickling -------------------------------------------------------------

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        # MappingProxyType is not picklable; store as a plain dict.
        state["input"] = dict(self.input)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        state["input"] = types.MappingProxyType(state["input"])
        self.__dict__.update(state)

    # -- serialization --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize the Document to a plain dict."""
        return {
            "input": dict(self.input),
            "content": dict(self.content),
            "eval": dict(self.eval),
            "history": [rec._asdict() for rec in self.history],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        """Reconstruct a Document from a dict produced by ``to_dict``."""
        history = [StepRecord(**rec) for rec in data.get("history", [])]
        return cls(
            input=data["input"],
            content=data.get("content", {}),
            eval=data.get("eval", {"ground_truth": None, "scores": None}),
            history=history,
        )
