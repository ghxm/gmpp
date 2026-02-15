# API Reference

Public classes and functions in gmpp. All imports below assume
`import gmpp` or import from the specific submodule.

## gmpp.document

### Document

```python
@dataclass
class Document:
    input: MappingProxyType[str, Any]   # frozen original data
    content: dict[str, Any]             # mutable working state
    eval: dict[str, Any]                # ground truth and scores
    history: list[StepRecord]           # processing provenance
```

**Constructor**: `Document(input={"html": ..., "doc_id": ...})`.
Accepts a regular dict for `input` and freezes it automatically.
If `content` is not provided, it is initialized as a mutable copy of `input`.

**Methods**:

- `to_dict() -> dict[str, Any]` -- Serialize to a plain dict.
- `Document.from_dict(data) -> Document` -- Reconstruct from a dict.

### StepRecord

```python
class StepRecord(NamedTuple):
    component_name: str
    output_field: str
    timestamp: str          # ISO 8601
    duration_s: float
    params: dict[str, Any]
```

Record of a single processing step. Appended to `doc.history` by the Pipeline.

---

## gmpp.component

### Component

```python
class Component(ABC):
    output_field: str       # class attribute, must be set by subclass
```

Abstract base class for all pipeline components.

**Abstract methods**:

- `process(doc: Document) -> Document` -- Process a single document.

**Optional overrides**:

- `setup(corpus: list[Document]) -> None` -- Called once before corpus processing.

**Inherited methods** (no reimplementation needed):

- `name -> str` -- Property returning the class name.
- `get_params() -> dict[str, Any]` -- Returns constructor parameter names and current values.
- `set_params(**params) -> None` -- Sets attributes for given parameter names.
- `to_dict() -> dict[str, Any]` -- Serializes to `{"name": ..., "params": {...}}`.
- `Component.from_dict(config) -> Component` -- Reconstructs via registry.

---

## gmpp.pipeline

### Pipeline

```python
class Pipeline:
    components: list[Component]
```

**Constructor**: `Pipeline(components: list[Component])`.

**Methods**:

- `run(doc: Document) -> Document` -- Process one Document through all components.
  Appends a `StepRecord` to `doc.history` after each step.

- `run_corpus(docs: list[Document]) -> list[Document]` -- Process a list of
  Documents. Calls `setup(docs)` on each component first. Warns if multiple
  components write to the same `output_field`.

- `to_config() -> dict[str, Any]` -- Serialize the pipeline to a config dict
  including component specs, Python version, and timestamp.

- `Pipeline.from_config(config: dict) -> Pipeline` -- Reconstruct a Pipeline
  from a config dict.

**Dunder methods**: `__repr__`, `__len__`, `__getitem__`.

---

## gmpp.registry

### Decorators

- `register_component(name: str) -> Callable` -- Class decorator. Registers a
  Component subclass under the given name.

- `register_metric(name: str) -> Callable` -- Function decorator. Registers a
  metric callable under the given name.

### Lookup and factory

- `get_component(name: str) -> type` -- Returns the Component class. Raises
  `KeyError` if not found.

- `get_metric(name: str) -> Callable[..., float]` -- Returns the metric
  callable. Raises `KeyError` if not found.

- `create_component(name: str, **params) -> Component` -- Instantiates a
  component by registered name with the given parameters.

- `list_components() -> dict[str, type]` -- Returns a copy of the component
  registry.

- `list_metrics() -> dict[str, Callable[..., float]]` -- Returns a copy of
  the metric registry.

---

## gmpp.eval

### evaluate

```python
def evaluate(
    doc: Document,
    metrics: list[str] | None = None,
    prediction_field: str = "text",
) -> Document
```

Score a single Document against its ground truth. Computes each metric and
stores results in `doc.eval["scores"]`. Returns the mutated Document.

**Raises**: `ValueError` if `doc.eval["ground_truth"]` is None.

### evaluate_corpus

```python
def evaluate_corpus(
    docs: list[Document],
    metrics: list[str] | None = None,
    prediction_field: str = "text",
) -> dict
```

Evaluate a list of Documents and aggregate scores. Returns a dict with:

- `"per_doc"`: list of `{"doc_id": str, "scores": dict}`.
- `"aggregate"`: dict of `{metric_name: {"mean": float, "median": float, "std": float}}`.

---

## gmpp.io

### load_corpus

```python
def load_corpus(
    path: str | Path,
    ground_truth: str | Path | None = None,
) -> list[Document]
```

Load Documents from a directory of `.html` files or a CSV manifest. Optionally
attach ground truth from a directory of `.txt` files matched by `doc_id`.

### save_results

```python
def save_results(
    docs: list[Document],
    output_dir: str | Path,
    config: dict | None = None,
) -> None
```

Write per-document results to `output_dir/results/{doc_id}.json`, a manifest
CSV, and optionally a config sidecar.

### load_results

```python
def load_results(output_dir: str | Path) -> list[Document]
```

Reconstruct Documents from `output_dir/results/*.json`.

### save_eval

```python
def save_eval(
    docs: list[Document],
    output_dir: str | Path,
    aggregate: dict,
) -> None
```

Write `eval/scores.csv` and `eval/aggregates.json` to the output directory.

---

## Built-in components

All built-in components are in `gmpp.components.*` and registered automatically
on import. See [Components Reference](components.md) for parameters and usage.

| Class         | Module                          | Registered name  |
|---------------|---------------------------------|------------------|
| `Trafilatura` | `gmpp.components.trafilatura`   | `"trafilatura"`  |
| `Readability` | `gmpp.components.readability`   | `"readability"`  |
| `JusText`     | `gmpp.components.justext`       | `"justext"`      |
| `Newspaper`   | `gmpp.components.newspaper`     | `"newspaper"`    |
| `Inscriptis`  | `gmpp.components.inscriptis`    | `"inscriptis"`   |

## Built-in metrics

| Function           | Registered name      | Dependencies         |
|--------------------|----------------------|----------------------|
| `rouge_lsum`       | `"rouge_lsum"`       | `rouge-score`        |
| `levenshtein`      | `"levenshtein"`      | `python-Levenshtein` |
| `token_precision`  | `"token_precision"`  | None                 |
| `token_recall`     | `"token_recall"`     | None                 |
| `token_f1`         | `"token_f1"`         | None                 |
