"""Evaluation metrics and corpus-level scoring for gmpp."""

import statistics

from gmpp.document import Document
from gmpp.registry import get_metric, list_metrics, register_metric


# -- Built-in metrics ---------------------------------------------------------


@register_metric("rouge_lsum")
def rouge_lsum(predicted: str, reference: str) -> float:
    """ROUGE-LSum F-measure between predicted and reference texts."""
    try:
        from rouge_score import rouge_scorer
    except ImportError:
        raise ImportError(
            "rouge_score is required for the rouge_lsum metric. "
            "Install it with: pip install gmpp[eval]"
        ) from None

    if not hasattr(rouge_lsum, "_scorer"):
        rouge_lsum._scorer = rouge_scorer.RougeScorer(
            ["rougeLsum"], use_stemmer=True
        )
    scores = rouge_lsum._scorer.score(reference, predicted)
    return scores["rougeLsum"].fmeasure


@register_metric("levenshtein")
def levenshtein(predicted: str, reference: str) -> float:
    """Normalized Levenshtein similarity (1 - distance / max_len)."""
    try:
        import Levenshtein as lev
    except ImportError:
        raise ImportError(
            "python-Levenshtein is required for the levenshtein metric. "
            "Install it with: pip install gmpp[eval]"
        ) from None

    if len(predicted) == 0 and len(reference) == 0:
        return 1.0

    dist = lev.distance(predicted, reference)
    max_len = max(len(predicted), len(reference))
    return 1.0 - dist / max_len


@register_metric("token_precision")
def token_precision(predicted: str, reference: str) -> float:
    """Precision of predicted tokens against reference tokens (whitespace split)."""
    predicted_tokens = predicted.split()
    reference_tokens = set(reference.split())

    if not predicted_tokens:
        return 0.0

    hits = sum(1 for t in predicted_tokens if t in reference_tokens)
    return hits / len(predicted_tokens)


@register_metric("token_recall")
def token_recall(predicted: str, reference: str) -> float:
    """Recall of predicted tokens against reference tokens (whitespace split)."""
    reference_tokens = reference.split()
    predicted_tokens = set(predicted.split())

    if not reference_tokens:
        return 0.0

    hits = sum(1 for t in reference_tokens if t in predicted_tokens)
    return hits / len(reference_tokens)


@register_metric("token_f1")
def token_f1(predicted: str, reference: str) -> float:
    """Harmonic mean of token precision and token recall."""
    p = token_precision(predicted, reference)
    r = token_recall(predicted, reference)

    if p + r == 0.0:
        return 0.0

    return 2 * p * r / (p + r)


@register_metric("jaccard")
def jaccard(predicted: str, reference: str) -> float:
    """Jaccard similarity over token sets (|A & B| / |A | B|)."""
    pred_tokens = set(predicted.split())
    ref_tokens = set(reference.split())

    if not pred_tokens and not ref_tokens:
        return 1.0

    intersection = pred_tokens & ref_tokens
    union = pred_tokens | ref_tokens
    return len(intersection) / len(union)


@register_metric("cosine")
def cosine(predicted: str, reference: str) -> float:
    """Cosine similarity over token frequency vectors."""
    from collections import Counter
    import math

    pred_counts = Counter(predicted.split())
    ref_counts = Counter(reference.split())

    if not pred_counts and not ref_counts:
        return 1.0
    if not pred_counts or not ref_counts:
        return 0.0

    all_tokens = set(pred_counts) | set(ref_counts)
    dot = sum(pred_counts[t] * ref_counts[t] for t in all_tokens)
    norm_pred = math.sqrt(sum(c * c for c in pred_counts.values()))
    norm_ref = math.sqrt(sum(c * c for c in ref_counts.values()))

    if norm_pred == 0.0 or norm_ref == 0.0:
        return 0.0

    return dot / (norm_pred * norm_ref)


# -- Document-level and corpus-level evaluation --------------------------------


def evaluate(
    doc: Document,
    metrics: list[str] | None = None,
    prediction_field: str = "text",
) -> Document:
    """Score a single Document against its ground truth.

    Computes each requested metric and stores the results in
    ``doc.eval["scores"]``.  The Document is mutated in place and returned.

    Args:
        doc: Document with ground truth set in ``doc.eval["ground_truth"]``.
        metrics: Metric names to compute.  If *None*, all registered metrics
            are used.
        prediction_field: Key in ``doc.content`` holding the predicted text.

    Returns:
        The same Document with ``doc.eval["scores"]`` populated.

    Raises:
        ValueError: If ``doc.eval["ground_truth"]`` is None.
    """
    if doc.eval["ground_truth"] is None:
        raise ValueError(
            "Cannot evaluate: doc.eval['ground_truth'] is None. "
            "Set ground truth before calling evaluate()."
        )

    if prediction_field not in doc.content:
        raise ValueError(
            f"Prediction field {prediction_field!r} not found in doc.content. "
            f"Available fields: {list(doc.content)}"
        )

    predicted = doc.content[prediction_field]
    reference = doc.eval["ground_truth"]

    if not isinstance(predicted, str):
        raise TypeError(
            f"Expected predicted text to be str, got {type(predicted).__name__}."
        )
    if not isinstance(reference, str):
        raise TypeError(
            f"Expected ground truth to be str, got {type(reference).__name__}."
        )

    if metrics is None:
        metric_fns = list_metrics()
    else:
        metric_fns = {name: get_metric(name) for name in metrics}

    scores: dict[str, float] = {}
    for name, fn in metric_fns.items():
        scores[name] = fn(predicted, reference)

    doc.eval["scores"] = scores
    return doc


def evaluate_corpus(
    docs: list[Document],
    metrics: list[str] | None = None,
    prediction_field: str = "text",
) -> dict:
    """Evaluate a list of Documents and aggregate scores.

    Calls :func:`evaluate` on each document, then computes mean, median, and
    standard deviation for every metric across the corpus.

    Args:
        docs: Documents to evaluate (each must have ground truth set).
        metrics: Metric names to compute.  If *None*, all registered metrics.
        prediction_field: Key in ``doc.content`` for predicted text.

    Returns:
        A dict with keys ``"per_doc"`` (list of per-document score dicts) and
        ``"aggregate"`` (dict of metric name to mean/median/std).
    """
    per_doc: list[dict] = []

    for doc in docs:
        evaluate(doc, metrics=metrics, prediction_field=prediction_field)
        doc_id = doc.input.get("doc_id", None)
        per_doc.append({"doc_id": doc_id, "scores": dict(doc.eval["scores"])})

    # Aggregate across the corpus.
    if not per_doc:
        return {"per_doc": per_doc, "aggregate": {}}

    # Collect all metric names from the first doc (they are identical).
    metric_names = list(per_doc[0]["scores"].keys())
    aggregate: dict[str, dict[str, float]] = {}

    for name in metric_names:
        values = [entry["scores"][name] for entry in per_doc]
        aggregate[name] = {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

    return {"per_doc": per_doc, "aggregate": aggregate}
