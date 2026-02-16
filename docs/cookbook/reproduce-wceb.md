# Reproduce WCEB benchmark results

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
