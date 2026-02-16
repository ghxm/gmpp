# Metrics Reference

gmpp includes built-in metrics for evaluating extraction quality by comparing
predicted text against ground truth. All metrics follow the same signature:
`(predicted: str, reference: str) -> float`.

## Built-in metrics

### rouge_lsum

ROUGE-LSum F-measure. The standard metric used in web content extraction
evaluation (Bevendorff et al., SIGIR 2023). Measures overlap of longest common
subsequences at the summary level.

**Range**: 0.0 to 1.0 (higher is better).

**Requires**: `pip install gmpp[eval]` (installs `rouge-score`).

### levenshtein

Normalized Levenshtein similarity, computed as `1 - (edit_distance / max_length)`.
A character-level metric that captures fine-grained differences.

**Range**: 0.0 to 1.0 (higher is better, 1.0 means identical strings).

**Requires**: `pip install gmpp[eval]` (installs `python-Levenshtein`).

### token_precision

Precision of predicted tokens against reference tokens (whitespace-split).
Measures what fraction of predicted tokens appear in the reference.

**Range**: 0.0 to 1.0 (higher is better).

**Requires**: No additional dependencies.

### token_recall

Recall of predicted tokens against reference tokens (whitespace-split).
Measures what fraction of reference tokens appear in the prediction.

**Range**: 0.0 to 1.0 (higher is better).

**Requires**: No additional dependencies.

### token_f1

Harmonic mean of token precision and token recall.

**Range**: 0.0 to 1.0 (higher is better).

**Requires**: No additional dependencies.

### jaccard

Jaccard similarity over token sets: `|A & B| / |A | B|`. Measures the
proportion of shared unique tokens between predicted and reference text.
Unlike token F1, Jaccard treats precision and recall symmetrically.

**Range**: 0.0 to 1.0 (higher is better).

**Requires**: No additional dependencies.

### cosine

Cosine similarity over token frequency vectors. Computes the angle between
bag-of-words TF vectors, making it sensitive to token frequency distributions
rather than just token presence.

**Range**: 0.0 to 1.0 (higher is better).

**Requires**: No additional dependencies.

## Using metrics

### Document-level evaluation

```python
from gmpp.eval import evaluate
from gmpp.document import Document

doc = Document(input={"html": "...", "doc_id": "page_001"})
doc.content["text"] = "Extracted text here."
doc.eval["ground_truth"] = "Reference text here."

evaluate(doc, metrics=["rouge_lsum", "levenshtein"])
print(doc.eval["scores"])
# {"rouge_lsum": 0.85, "levenshtein": 0.72}
```

### Corpus-level evaluation

```python
from gmpp.eval import evaluate_corpus

scores = evaluate_corpus(docs, metrics=["rouge_lsum", "token_f1"])

# Per-document scores
for entry in scores["per_doc"]:
    print(entry["doc_id"], entry["scores"])

# Corpus aggregates (mean, median, std)
print(scores["aggregate"])
# {"rouge_lsum": {"mean": 0.82, "median": 0.85, "std": 0.12}, ...}
```

### Using all metrics

Pass `metrics=None` (or omit the argument) to compute all registered metrics:

```python
evaluate(doc)  # computes all registered metrics (rouge_lsum, levenshtein, token_*, jaccard, cosine)
```

## Writing a custom metric

Any callable with the signature `(predicted: str, reference: str) -> float`
can be registered as a metric:

```python
from gmpp.registry import register_metric

@register_metric("char_compression")
def char_compression(predicted: str, reference: str) -> float:
    """Ratio of predicted length to reference length (compression measure)."""
    if len(reference) == 0:
        return 0.0
    return min(len(predicted) / len(reference), 1.0)
```

After registration, use it by name like any built-in metric:

```python
evaluate(doc, metrics=["char_compression"])
```

Document your convention for the return value: whether higher is better
or lower is better, and the expected range.
