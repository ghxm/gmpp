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
that creates multiple pipeline configs and runs each one. This allows for a "multiverse layer" over the core pipeline execution, where you can systematically explore different parameter combinations and compare their results.

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

## Route pages to different extractors

Some corpora contain a mix of page types (articles, forum threads, link lists)
where no single extractor performs best across all of them. A router component
can classify each page and delegate to the appropriate extractor.

This works without any changes to gmpp itself. A component's `process()` method
can instantiate and call other components internally.

```python
from typing import Any
from html.parser import HTMLParser

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component
from gmpp import create_component


def classify_page(html: str) -> str:
    """Classify a page as 'article', 'forum', or 'listing' using HTML structure."""

    class TagCounter(HTMLParser):
        def __init__(self):
            super().__init__()
            self.counts: dict[str, int] = {}
            self.total_text_len = 0
            self.link_text_len = 0
            self._in_a = False

        def handle_starttag(self, tag, attrs):
            self.counts[tag] = self.counts.get(tag, 0) + 1
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            if any(kw in cls.lower() for kw in ("comment", "post", "reply")):
                self.counts["_forum_class"] = self.counts.get("_forum_class", 0) + 1
            if tag == "meta":
                prop = attrs_dict.get("property", "")
                content = attrs_dict.get("content", "")
                if prop == "og:type" and "article" in content:
                    self.counts["_og_article"] = 1
            if tag == "a":
                self._in_a = True

        def handle_endtag(self, tag):
            if tag == "a":
                self._in_a = False

        def handle_data(self, data):
            stripped = data.strip()
            self.total_text_len += len(stripped)
            if self._in_a:
                self.link_text_len += len(stripped)

    counter = TagCounter()
    try:
        counter.feed(html)
    except Exception:
        return "article"

    c = counter.counts
    scores = {"article": 0.0, "forum": 0.0, "listing": 0.0}

    scores["article"] += 3.0 * c.get("article", 0)
    scores["article"] += 3.0 * c.get("_og_article", 0)
    scores["article"] += 1.0 * min(c.get("p", 0), 10)
    scores["article"] += 1.0 * c.get("time", 0)

    scores["forum"] += 1.5 * min(c.get("blockquote", 0), 5)
    scores["forum"] += 2.0 * min(c.get("_forum_class", 0), 5)

    if counter.total_text_len > 0:
        link_ratio = counter.link_text_len / counter.total_text_len
        if link_ratio > 0.5:
            scores["listing"] += 5.0
    scores["listing"] += 0.5 * min(c.get("li", 0) // 5, 5)

    return max(scores, key=lambda k: scores[k])


@register_component("page_router")
class PageRouter(Component):
    """Route to different extractors based on detected page structure."""

    output_field = "text"

    def __init__(
        self,
        article_extractor: str = "trafilatura",
        forum_extractor: str = "readability",
        listing_extractor: str = "inscriptis",
        article_params: dict[str, Any] | None = None,
        forum_params: dict[str, Any] | None = None,
        listing_params: dict[str, Any] | None = None,
    ) -> None:
        self.article_extractor = article_extractor
        self.forum_extractor = forum_extractor
        self.listing_extractor = listing_extractor
        self.article_params = article_params or {}
        self.forum_params = forum_params or {}
        self.listing_params = listing_params or {}

    def process(self, doc: Document) -> Document:
        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            doc.content["page_type"] = "unknown"
            return doc

        page_type = classify_page(html)
        doc.content["page_type"] = page_type

        extractor_map = {
            "article": (self.article_extractor, self.article_params),
            "forum": (self.forum_extractor, self.forum_params),
            "listing": (self.listing_extractor, self.listing_params),
        }
        name, params = extractor_map[page_type]
        extractor = create_component(name, **params)
        doc = extractor.process(doc)
        return doc
```

Since the router is a regular component, it composes naturally with other
pipeline steps. For example, you can add a common preprocessing step before
the router and a postprocessing step after it:

```python
import re

from gmpp import Pipeline
from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component
from gmpp.io import load_corpus
from gmpp.eval import evaluate_corpus


@register_component("script_remover")
class ScriptRemover(Component):
    """Remove script and style tags before extraction."""

    output_field = "html"

    def process(self, doc: Document) -> Document:
        html = doc.content.get("html", "")
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        doc.content[self.output_field] = html
        return doc


@register_component("whitespace_normalizer")
class WhitespaceNormalizer(Component):
    """Collapse runs of whitespace in extracted text."""

    output_field = "text"

    def process(self, doc: Document) -> Document:
        text = doc.content.get("text", "")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        doc.content[self.output_field] = text.strip()
        return doc


# 1. Clean HTML  ->  2. Route to best extractor  ->  3. Normalize output
pipe = Pipeline([
    ScriptRemover(),
    PageRouter(
        article_extractor="trafilatura",
        forum_extractor="readability",
        listing_extractor="inscriptis",
        article_params={"favor_precision": True},
    ),
    WhitespaceNormalizer(),
])

docs = load_corpus("./htmls/", ground_truth="./gt/")
results = pipe.run_corpus(docs)

# Inspect what the router decided for each page
for doc in results:
    print(f"{doc.input['doc_id']:30s} -> {doc.content['page_type']}")

# Evaluate as usual
scores = evaluate_corpus(results, metrics=["rouge_lsum"])
```

Each step reads from and writes to `doc.content`, so they chain naturally.
The preprocessing and postprocessing steps run for every document, while
the router picks a different extractor per page.

A few things to note:

- The constructor takes extractor names as strings (not instances), so
  `get_params()` and config serialization work out of the box.
- The router stores the detected page type in `doc.content["page_type"]`
  for downstream inspection.
- Inner component calls bypass the Pipeline, so they do not appear as
  separate entries in `doc.history`. The router shows up as a single step.

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
