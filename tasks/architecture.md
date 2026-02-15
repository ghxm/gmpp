# gmpp — generic multi-purpose parsing tool

## Name
- **gmpp**
- generic multi-parser pipeline *or* generic multi-purpose parser

## Concept
- Lightweight wrapper around HTML content extraction libraries (trafilatura, jusText, readability, newspaper4k, inscriptis, custom BS4 parsers, ...)
- Chain multiple processing steps into pipelines (e.g., template induction → simplification → extraction)
- Evaluate extraction quality against ground truth with standardized metrics
- "spaCy of HTML parsing" — common interface, pluggable backends, reproducible configs

## Use case
- Systematically compare different parsing strategies and parameter settings
- Chain preprocessing and extraction steps in reproducible pipelines
- Plug in new parsers with minimal boilerplate (subclass, implement one method)
- Evaluate against ground truth using established metrics (ROUGE-LSum, Levenshtein)
- The external multiverse layer orchestrates multiple pipeline configs; gmpp handles single-pipeline execution + eval

---

## Core classes

### Document
- Mutable data container that flows through the pipeline
- **`doc.input`** — frozen after creation, original data
	- `html`, `doc_id`, `url`, `domain`, any other source metadata
	- Never modified by components — always available for diffing, rerunning, serialization
- **`doc.content`** — mutable working state, components read/write here
	- Initialized from `doc.input` (e.g., `content["html"]` = `input["html"]`)
	- `output_field` maps into this namespace (e.g., `output_field = "text"` → `doc.content["text"]`)
	- Intermediate results live here: `cleaned_html`, `text`, `tables`, etc.
- **`doc.eval`** — evaluation data
	- `ground_truth: str | None`, `scores: dict | None`
- **`doc.history`** — `list[StepRecord]`, provenance tracking
- All four are just dicts (except history = list) — no new classes
- Pure data carrier — no processing methods

### Component (base class)
- One processing step wrapping a specific library

#### Required
- `output_field: str` — class attribute, declares which `doc.content` key this writes to
- `process(doc) → doc` — main logic; reads whatever it needs from Document, writes to `output_field`

#### Optional
- `setup(corpus)` — called once before processing; for corpus-aware components (template induction)

#### Inherited (no reimplementation needed)
- `name: str` — identifier
- `get_params() → dict` / `set_params()` — scikit-learn style
- `to_dict()` / `from_dict()` — config serialization
- `__repr__` — shows name + params

#### Writing a new component
1. Subclass `Component`
2. Set `output_field`
3. Implement `process(doc)`

### Pipeline
- Ordered list of Components
- `pipe.run(doc) → doc` — single document through all steps
- `pipe.run_corpus(docs) → list[doc]` — batch; calls `setup(corpus)` first, then processes each doc
- `pipe.to_config() → dict` — full spec: components, params, library versions, Python version, timestamp
- `Pipeline.from_config(config) → Pipeline` — reconstruct via registry
- Tracks which fields have been written (debug/introspection); warns but does not enforce contracts

### Registry
- `dict[str, type[Component]]` + `@register_component(name)` decorator
- `create_component(name, **params) → Component` factory
- Enables JSON config → Pipeline reconstruction
- Optional — researchers can pass component instances directly

---

## Evaluation (`gmpp.eval`)

### Design
- Separate module — Pipeline knows nothing about eval
- Ground truth lives on the Document (`doc.ground_truth`), not in external files
- **Eval is external to Document**: `evaluate(doc, metrics=...) → dict` reads `doc.content["text"]` vs `doc.eval["ground_truth"]`, stores result in `doc.eval["scores"]`
- `evaluate_corpus(docs) → DataFrame` — calls `evaluate()` per doc, then aggregates (mean, median, std)
- No join logic needed — ground truth travels with the document
- Pipeline knows nothing about eval

### Built-in metrics
- **ROUGE-LSum** — standard in web content extraction eval (Bevendorff et al. 2023)
- **Levenshtein distance** (normalized) — character-level
- **Token-level Precision / Recall / F1**
- Custom metrics: any `(predicted: str, reference: str) → float` callable, register via `@register_metric(name)`

---

## CLI

### Commands

```bash
gmpp run <config.json> --input <dir|manifest.csv> --output <dir> [--parallelism N]
```
Run a pipeline on a corpus. Writes results + config sidecar to output dir.

```bash
gmpp eval <output_dir> --ground-truth <dir|csv> [--metrics rouge_lsum,levenshtein]
```
Evaluate results against ground truth. Hydrates `doc.ground_truth` from files, scores, writes to `eval/`.

```bash
gmpp list                    # registered components + their params
gmpp show <config.json>      # validate + pretty-print pipeline config
gmpp inspect <output_dir>    # provenance: what ran, when, timing
```

### Input formats
- **Directory**: `.html` files, `doc_id` = filename stem
- **Manifest CSV**: `doc_id,path,url,ground_truth_path`
- **Python API**: `list[Document]` directly

### Output structure
```
output_dir/
├── config.json              # pipeline config (auto-generated)
├── results/
│   ├── doc_001.json         # per-doc: text, metadata, history
│   └── ...
└── eval/                    # only after gmpp eval
    ├── scores.csv           # per-doc metric scores
    └── aggregates.json      # corpus-level stats
```
Self-contained and shareable as-is.

---

## Design principles

### gmpp does
- Common interface around different parsers
- Pipeline chaining with provenance tracking
- Config serialization for reproducibility
- Standardized evaluation against ground truth
- CLI for batch processing

### gmpp does NOT do
- Experiment grid / multiverse management → external
- Cross-pipeline comparison / visualization → external
- No dedicated abstraction for strategy selection or fallback chains — but both are trivially implementable as Components (e.g., a routing component that checks `doc.input["domain"]` and delegates to different backends, or a component that tries extractor A and falls back to B)

### Key constraints
- Pipeline validation is lightweight (warn, don't enforce)
- Components are responsible for handling the Document state they receive
- In-place operations supported (`output_field = "html"` overwrites `doc.content["html"]`, but `doc.input["html"]` is always preserved)
- Corpus-level components use `setup(corpus)`, same interface otherwise

---

## Initial backends
| Component | Library | Type | Notes |
|---|---|---|---|
| `Trafilatura` | trafilatura | extractor | Best general-purpose |
| `Readability` | readability-lxml | extractor | Strong median performance |
| `JusText` | jusText | extractor | Linguistically principled |
| `Newspaper` | newspaper4k | extractor | Article-focused, rich metadata |
| `Inscriptis` | inscriptis | baseline | No boilerplate removal (raw → text) |

---

## Validation & test data

### WCEB (Web Content Extraction Benchmark)
- https://github.com/chatnoir-eu/web-content-extraction-benchmark
- Bevendorff et al. (SIGIR 2023): "An Empirical Comparison of Web Content Extraction Algorithms"
- **Validation target**: reproduce WCEB's published ROUGE-LSum and Levenshtein scores for single-component pipelines (trafilatura, readability, jusText, etc.) — if scores match within tolerance, gmpp is working correctly
- **Development test data**: 8 annotated datasets (`datasets/combined.tar.xz`), HTML pages with ground truth text, diverse page types (news, forums, product pages)
- **Validates full lifecycle**: document loading → component wrappers → pipeline execution → eval metrics → output format

---

## Documentation plan

### README.md
- One-paragraph description: what gmpp is, who it's for
- Quick install: `pip install gmpp`
- Minimal example (5-10 lines): build a pipeline, run it, evaluate
- Link to full docs

```markdown
# gmpp

Lightweight framework for comparing HTML content extraction strategies.
Wrap different parsers (trafilatura, readability, jusText, ...) in a common
pipeline interface with built-in evaluation.

## Install
pip install gmpp

## Quick start
from gmpp import Pipeline, Trafilatura, Readability, load_corpus, evaluate_corpus

docs = load_corpus("./htmls/", ground_truth="./gt/")
pipe = Pipeline([Trafilatura(favor_precision=False)])
results = pipe.run_corpus(docs)
scores = evaluate_corpus(results, metrics=["rouge_lsum"])

## CLI
gmpp run config.json --input ./htmls/ --output ./results/
gmpp eval ./results/ --ground-truth ./gt/

## Docs
https://gmpp.readthedocs.io (or GitHub Pages)
```

### CONTRIBUTING.md
- How to add a new component (step-by-step with example)
- How to add a new metric
- Dev setup: clone, `pip install -e ".[dev]"`, run tests
- Testing: `pytest`, use WCEB test data
- Code style: ruff/black, type hints required
- PR process: branch, test, PR

```markdown
# Contributing to gmpp

## Adding a new component
1. Create `gmpp/components/my_parser.py`
2. Subclass `Component`, set `output_field`, implement `process(doc)`
3. Decorate with `@register_component("my_parser")`
4. Add tests using WCEB test data
5. Add entry to docs

## Adding a new metric
1. Write a function: `(predicted: str, reference: str) → float`
2. Decorate with `@register_metric("my_metric")`

## Development setup
git clone ...
cd gmpp
pip install -e ".[dev]"
pytest

## Code style
- ruff for linting, black for formatting
- Type hints on all public APIs
- Docstrings on all public classes/functions
```

### Documentation site (mkdocs or sphinx)
- **Getting started**: install, first pipeline, first eval
- **Concepts**: Document, Component, Pipeline, Registry — one page each, short
- **Components reference**: auto-generated from docstrings, one page per built-in component showing accepted params
- **Metrics reference**: built-in metrics + how to add custom ones
- **CLI reference**: all commands with examples
- **Config format**: JSON schema with annotated example
- **Cookbook**: common recipes
	- "Compare trafilatura vs readability on a corpus"
	- "Add a preprocessing step before extraction"
	- "Write a custom component"
	- "Run a parameter sweep" (multiverse layer example)
	- "Reproduce WCEB benchmark results"
- **API reference**: auto-generated from type hints + docstrings
- Host on GitHub Pages or ReadTheDocs

---

## External multiverse layer (not part of gmpp)

### Python API
```python
pipe_a = Pipeline([TemplateInduction(...), Simplify(...), Trafilatura(favor_precision=False)])
pipe_b = Pipeline([Simplify(...), Trafilatura(favor_precision=True)])
pipe_c = Pipeline([Readability()])

docs = load_corpus("./htmls/", ground_truth="./gt/")

for pipe in [pipe_a, pipe_b, pipe_c]:
    results = pipe.run_corpus(docs)
    scores = evaluate_corpus(results, metrics=["rouge_lsum", "levenshtein"])
    # compare, visualize across configs...
```

### CLI equivalent
```bash
for config in configs/*.json; do
    name=$(basename "$config" .json)
    gmpp run "$config" --input ./htmls/ --output "./results/$name/"
    gmpp eval "./results/$name/" --ground-truth ./ground_truth/
done
```