# Compare trafilatura vs readability on a corpus

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
