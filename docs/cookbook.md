# Cookbook

Practical recipes for common tasks with gmpp.

## Compare trafilatura vs readability on a corpus

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.components.readability import Readability
from gmpp.io import load_corpus
from gmpp.eval import evaluate_corpus

docs = load_corpus("./htmls/", ground_truth="./gt/")

pipelines = {
    "trafilatura_precision": Pipeline([Trafilatura(favor_precision=True)]),
    "trafilatura_recall": Pipeline([Trafilatura(favor_recall=True)]),
    "readability": Pipeline([Readability()]),
}

for name, pipe in pipelines.items():
    # Reload docs for each pipeline (both pipeline and evaluation mutate docs)
    docs = load_corpus("./htmls/", ground_truth="./gt/")
    results = pipe.run_corpus(docs)
    scores = evaluate_corpus(results, metrics=["rouge_lsum", "levenshtein"])

    agg = scores["aggregate"]
    print(f"{name}:")
    for metric, stats in agg.items():
        print(f"  {metric}: mean={stats['mean']:.3f}, std={stats['std']:.3f}")
```

## Add a preprocessing step before extraction

If your HTML needs cleaning before extraction (e.g., removing navigation
elements, ads, or scripts), you can add a preprocessing component to the
pipeline. This component writes back to `"html"`, which the extractor then
reads from.

```python
from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component

@register_component("script_remover")
class ScriptRemover(Component):
    """Remove script and style tags from HTML."""

    output_field = "html"  # overwrites content["html"]

    def process(self, doc: Document) -> Document:
        import re

        html = doc.content.get("html", "")
        # Remove script and style blocks
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        doc.content[self.output_field] = html
        return doc


# Use it in a pipeline before the extractor
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura

pipe = Pipeline([
    ScriptRemover(),
    Trafilatura(favor_precision=True),
])
```

The original HTML is always preserved in `doc.input["html"]` regardless of
what preprocessing does to `doc.content["html"]`.

## Write a custom component

See [Component concepts](concepts/component.md) for a detailed walkthrough.
The minimal version:

```python
from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component

@register_component("my_extractor")
class MyExtractor(Component):
    output_field = "text"

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def process(self, doc: Document) -> Document:
        html = doc.content.get("html", "")
        # Your extraction logic here
        doc.content[self.output_field] = extracted_text
        return doc
```

Requirements:

1. Subclass `Component`.
2. Set `output_field`.
3. Implement `process(doc)` -- read from `doc.content`, write to `doc.content[self.output_field]`.
4. Store constructor parameters as instance attributes (for `get_params()` introspection).
5. Decorate with `@register_component("name")` if you want config serialization.

## Run a parameter sweep (multiverse layer)

gmpp handles single-pipeline execution. A parameter sweep is an external loop
that creates multiple pipeline configs and runs each one. This is what the
architecture calls the "multiverse layer".

### Python approach

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.io import load_corpus, save_results
from gmpp.eval import evaluate_corpus

# Define parameter grid
param_grid = [
    {"favor_precision": True, "include_tables": True},
    {"favor_precision": True, "include_tables": False},
    {"favor_precision": False, "favor_recall": True},
]

for i, params in enumerate(param_grid):
    docs = load_corpus("./htmls/", ground_truth="./gt/")
    pipe = Pipeline([Trafilatura(**params)])
    results = pipe.run_corpus(docs)
    scores = evaluate_corpus(results, metrics=["rouge_lsum"])

    # Save each run separately
    save_results(results, f"./output/run_{i:03d}/", config=pipe.to_config())

    agg = scores["aggregate"]
    print(f"Run {i} ({params}): rouge_lsum mean={agg['rouge_lsum']['mean']:.3f}")
```

### CLI approach

Generate config files for each parameter combination, then use a shell loop:

```bash
for config in configs/*.json; do
    name=$(basename "$config" .json)
    gmpp run "$config" --input ./htmls/ --output "./results/$name/"
    gmpp eval "./results/$name/" --ground-truth ./gt/
done
```

### Comparing across runs

After running multiple configurations, you can load and compare their
evaluation outputs:

```python
import json
from pathlib import Path

results_root = Path("./output/")
for run_dir in sorted(results_root.iterdir()):
    agg_path = run_dir / "eval" / "aggregates.json"
    config_path = run_dir / "config.json"

    if agg_path.exists():
        with open(agg_path) as f:
            agg = json.load(f)
        with open(config_path) as f:
            config = json.load(f)
        print(f"{run_dir.name}: {agg}")
```

## Reproduce WCEB benchmark results

The [WCEB (Web Content Extraction Benchmark)](https://github.com/chatnoir-eu/web-content-extraction-benchmark)
by Bevendorff et al. (SIGIR 2023) provides annotated HTML pages with ground
truth text across 8 datasets. You can use gmpp to reproduce their published
scores for individual extractors.

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.components.readability import Readability
from gmpp.components.justext import JusText
from gmpp.io import load_corpus
from gmpp.eval import evaluate_corpus

# Load WCEB data (adjust paths to your local copy)
docs = load_corpus("./wceb/html/", ground_truth="./wceb/ground_truth/")

extractors = {
    "trafilatura": Pipeline([Trafilatura(favor_precision=True)]),
    "readability": Pipeline([Readability()]),
    "justext": Pipeline([JusText()]),
}

for name, pipe in extractors.items():
    corpus = load_corpus("./wceb/html/", ground_truth="./wceb/ground_truth/")
    results = pipe.run_corpus(corpus)
    scores = evaluate_corpus(results, metrics=["rouge_lsum", "levenshtein"])

    agg = scores["aggregate"]
    print(f"\n{name}:")
    for metric, stats in agg.items():
        print(f"  {metric}: mean={stats['mean']:.3f}, median={stats['median']:.3f}")
```

If gmpp's scores match the published WCEB results within tolerance, the
component wrappers and evaluation metrics are working correctly. This serves
as an end-to-end validation of the framework.
