"""Pipeline — ordered sequence of Components applied to Documents."""

import logging
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Any

from gmpp.component import Component
from gmpp.document import Document, StepRecord

logger = logging.getLogger(__name__)


def _run_single(pipeline: "Pipeline", doc: Document) -> Document:
    """Top-level helper for ProcessPoolExecutor (must be picklable)."""
    return pipeline._run_safe(doc)


class Pipeline:
    """Ordered list of Components that processes Documents.

    Attributes:
        components: The processing steps in execution order.
    """

    def __init__(self, components: list[Component]) -> None:
        self.components = components

    # -- execution ------------------------------------------------------------

    def run(self, doc: Document) -> Document:
        """Run a single Document through all components in order.

        Raises on errors.  Use :meth:`run_corpus` for fault-tolerant batch
        processing.
        """
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

    def _run_safe(self, doc: Document) -> Document:
        """Run a single Document, catching errors for batch resilience.

        On failure the document is returned with empty output fields so that
        downstream code (e.g. evaluation) can handle it as a zero-score result.
        """
        try:
            return self.run(doc)
        except Exception as exc:
            doc_id = doc.input.get("doc_id", "<unknown>")
            logger.warning("Document %s failed: %s", doc_id, exc)
            for component in self.components:
                doc.content.setdefault(component.output_field, "")
            return doc

    def run_corpus(
        self, docs: list[Document], n_jobs: int = 1,
    ) -> list[Document]:
        """Run a list of Documents through the pipeline.

        Calls ``setup(docs)`` on each component first, then processes each
        document via ``run()``.  Individual document failures are logged and
        the document is returned with empty output fields rather than aborting
        the entire batch.

        Args:
            docs: Documents to process.
            n_jobs: Number of worker processes. 1 (default) runs sequentially.
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
        if n_jobs > 1:
            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                return list(executor.map(_run_single, [self] * len(docs), docs))
        return [self._run_safe(doc) for doc in docs]

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
