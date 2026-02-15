"""gmpp — lightweight framework for comparing HTML content extraction strategies."""

from gmpp.document import Document, StepRecord
from gmpp.component import Component
from gmpp.pipeline import Pipeline
from gmpp.registry import (
    register_component,
    register_metric,
    create_component,
    list_components,
    list_metrics,
)

__version__ = "0.1.0"

__all__ = [
    "Document",
    "StepRecord",
    "Component",
    "Pipeline",
    "register_component",
    "register_metric",
    "create_component",
    "list_components",
    "list_metrics",
    "__version__",
]
