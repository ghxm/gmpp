"""Pipeline — ordered sequence of Components applied to Documents."""

import sys
import time
import warnings
from datetime import datetime
from typing import Any

from gmpp.component import Component
from gmpp.document import Document, StepRecord


class Pipeline:
    """Ordered list of Components that processes Documents.

    Attributes:
        components: The processing steps in execution order.
    """

    def __init__(self, components: list[Component]) -> None:
        self.components = components

    # -- execution ------------------------------------------------------------

    def run(self, doc: Document) -> Document:
        """Run a single Document through all components in order."""
        for component in self.components:
            t0 = time.perf_counter()
            result = component.process(doc)
            duration = time.perf_counter() - t0

            if result is None:
                raise RuntimeError(
                    f"Component {component.name!r} returned None from process(). "
                    f"Did you forget to return the Document?"
                )
            doc = result

            record = StepRecord(
                component_name=component.name,
                output_field=component.output_field,
                timestamp=datetime.now().isoformat(),
                duration_s=round(duration, 6),
                params=component.get_params(),
            )
            doc.history.append(record)
        return doc

    def run_corpus(self, docs: list[Document]) -> list[Document]:
        """Run a list of Documents through the pipeline.

        Calls ``setup(docs)`` on each component first, then processes each
        document via ``run()``. Warns if a component overwrites a field
        previously written by another component.
        """
        # Setup phase
        for component in self.components:
            component.setup(docs)

        # Detect field overwrites
        fields_written: dict[str, str] = {}  # field -> component name
        for component in self.components:
            field = component.output_field
            if field in fields_written:
                warnings.warn(
                    f"Component {component.name!r} overwrites field "
                    f"{field!r} previously written by "
                    f"{fields_written[field]!r}.",
                    stacklevel=2,
                )
            fields_written[field] = component.name

        # Processing phase
        return [self.run(doc) for doc in docs]

    # -- serialization --------------------------------------------------------

    def to_config(self) -> dict[str, Any]:
        """Serialize the full pipeline configuration."""
        return {
            "components": [c.to_dict() for c in self.components],
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat(),
        }

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "Pipeline":
        """Reconstruct a Pipeline from a config dict."""
        components = [
            Component.from_dict(c) for c in config["components"]
        ]
        return cls(components)

    # -- dunder helpers -------------------------------------------------------

    def __repr__(self) -> str:
        return f"Pipeline({self.components!r})"

    def __len__(self) -> int:
        return len(self.components)

    def __getitem__(self, index: int) -> Component:
        return self.components[index]
