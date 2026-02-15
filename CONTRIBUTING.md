# Contributing to gmpp

## Development setup

```bash
git clone https://github.com/maxhaag/gmpp.git
cd gmpp
pip install -e ".[dev]"
pytest
```

This installs all parser backends, evaluation metrics, and dev tools (pytest, ruff).

## Adding a new component

1. Create a new file in `src/gmpp/components/`, e.g. `my_parser.py`.

2. Subclass `Component`, set `output_field`, implement `process(doc)`, and
   register with the decorator:

```python
"""MyParser component -- short description."""

from __future__ import annotations

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("my_parser")
class MyParser(Component):
    """What this parser does and when to use it."""

    output_field = "text"

    def __init__(self, some_param: str = "default") -> None:
        self.some_param = some_param

    def process(self, doc: Document) -> Document:
        import my_library  # lazy import so gmpp works without it

        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            return doc

        result = my_library.extract(html, option=self.some_param)
        doc.content[self.output_field] = result
        return doc
```

3. Add the module path to the `_COMPONENT_MODULES` list in
   `src/gmpp/components/__init__.py`:

```python
_COMPONENT_MODULES = [
    # ... existing modules ...
    "gmpp.components.my_parser",
]
```

4. If the library is an optional dependency, add it to `pyproject.toml`:

```toml
[project.optional-dependencies]
my_parser = ["my-library"]
```

   And include it in the `all` extra.

5. Write tests in `tests/` using WCEB test data or synthetic HTML.

6. Add an entry to the Components Reference in `docs/components.md`.

## Adding a new metric

1. Write a function with signature `(predicted: str, reference: str) -> float`.

2. Decorate it with `@register_metric` and place it in `src/gmpp/eval.py`
   (or a separate module that gets imported):

```python
from gmpp.registry import register_metric

@register_metric("my_metric")
def my_metric(predicted: str, reference: str) -> float:
    """What this metric measures."""
    # Return a float score (higher = better, or document the convention).
    return some_score
```

3. Add documentation to `docs/metrics.md`.

## Testing

Run all tests:

```bash
pytest
```

Run a specific test file:

```bash
pytest tests/test_pipeline.py
```

Tests use the WCEB (Web Content Extraction Benchmark) test data when available.
When writing tests for new components, include at least:

- A test with minimal/empty HTML input.
- A test with a realistic HTML page.
- A test that the component is discoverable via the registry.

## Code style

- **Linting**: ruff (configured in `pyproject.toml`, line length 88).
- **Type hints**: Required on all public function signatures.
- **Docstrings**: Required on all public classes and functions.
- **Imports**: Use lazy imports for optional dependencies inside `process()` methods,
  so that gmpp can be imported even when a backend library is not installed.

Check your code before submitting:

```bash
ruff check src/ tests/
```

## PR process

1. Create a feature branch from `main`.
2. Make your changes.
3. Run `pytest` and `ruff check` -- both must pass.
4. Open a pull request with a clear description of what the change does and why.
