"""Corpus I/O: loading documents, saving/loading results and evaluations."""

import csv
import json
from pathlib import Path

from gmpp.document import Document


def load_corpus(
    path: str | Path,
    ground_truth: str | Path | None = None,
) -> list[Document]:
    """Load a corpus of Documents from a directory or CSV manifest.

    Args:
        path: Either a directory containing ``.html`` files or a CSV manifest
            with at least ``doc_id`` and ``path`` columns.
        ground_truth: Optional directory of ground-truth ``.txt`` files (matched
            by doc_id) or *None* if ground truth is specified in the manifest.

    Returns:
        A list of Documents sorted by ``doc_id``.
    """
    path = Path(path)

    if path.is_dir():
        docs = _load_from_directory(path)
    else:
        docs = _load_from_manifest(path)

    # Attach ground truth from a directory if provided.
    if ground_truth is not None:
        gt_path = Path(ground_truth)
        if gt_path.is_dir():
            _attach_ground_truth_from_dir(docs, gt_path)

    docs.sort(key=lambda d: d.input.get("doc_id", ""))
    return docs


def _load_from_directory(directory: Path) -> list[Document]:
    """Load all .html files in *directory* as Documents."""
    docs: list[Document] = []
    for html_file in sorted(directory.glob("*.html")):
        doc_id = html_file.stem
        html_content = html_file.read_text(encoding="utf-8")
        doc = Document(
            input={"html": html_content, "doc_id": doc_id, "url": None}
        )
        docs.append(doc)
    return docs


def _load_from_manifest(manifest_path: Path) -> list[Document]:
    """Load Documents described by a CSV manifest.

    Expected columns: ``doc_id``, ``path``.
    Optional columns: ``url``, ``ground_truth_path``.
    """
    docs: list[Document] = []
    base_dir = manifest_path.parent

    with open(manifest_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            doc_id = row["doc_id"]
            html_path = base_dir / row["path"]
            html_content = html_path.read_text(encoding="utf-8")
            url = row.get("url") or None

            doc = Document(
                input={"html": html_content, "doc_id": doc_id, "url": url}
            )

            # Ground truth path in manifest takes precedence.
            gt_path_str = row.get("ground_truth_path")
            if gt_path_str:
                gt_file = base_dir / gt_path_str
                doc.eval["ground_truth"] = gt_file.read_text(encoding="utf-8")

            docs.append(doc)

    return docs


def _attach_ground_truth_from_dir(docs: list[Document], gt_dir: Path) -> None:
    """Match Documents to ``{doc_id}.txt`` files in *gt_dir*."""
    for doc in docs:
        doc_id = doc.input.get("doc_id")
        if doc_id is None:
            continue
        gt_file = gt_dir / f"{doc_id}.txt"
        if gt_file.exists():
            doc.eval["ground_truth"] = gt_file.read_text(encoding="utf-8")


# -- Saving and loading results -----------------------------------------------


def save_results(
    docs: list[Document],
    output_dir: str | Path,
    config: dict | None = None,
) -> None:
    """Write per-document results and an optional config sidecar.

    Creates ``output_dir/results/{doc_id}.json`` for every document,
    a ``results/manifest.csv`` listing all doc_ids, and optionally
    ``output_dir/config.json``.
    """
    output_dir = Path(output_dir)
    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    doc_ids: list[str] = []

    for doc in docs:
        doc_id = doc.input.get("doc_id", "unknown")
        doc_ids.append(doc_id)
        result_path = results_dir / f"{doc_id}.json"
        with open(result_path, "w", encoding="utf-8") as fh:
            json.dump(doc.to_dict(), fh, indent=2, ensure_ascii=False)

    # Manifest CSV.
    manifest_path = results_dir / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["doc_id"])
        for doc_id in doc_ids:
            writer.writerow([doc_id])

    # Config sidecar.
    if config is not None:
        config_path = output_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2, ensure_ascii=False)


def load_results(output_dir: str | Path) -> list[Document]:
    """Reconstruct Documents from ``output_dir/results/*.json``.

    Returns:
        A list of Documents sorted by ``doc_id``.
    """
    results_dir = Path(output_dir) / "results"
    docs: list[Document] = []

    for json_file in sorted(results_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as fh:
            data = json.load(fh)
        docs.append(Document.from_dict(data))

    docs.sort(key=lambda d: d.input.get("doc_id", ""))
    return docs


def save_eval(
    docs: list[Document],
    output_dir: str | Path,
    aggregate: dict,
) -> None:
    """Write evaluation outputs to ``output_dir/eval/``.

    Creates:
        - ``eval/scores.csv`` with per-document metric scores.
        - ``eval/aggregates.json`` with corpus-level statistics.
    """
    output_dir = Path(output_dir)
    eval_dir = output_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    # Determine metric names from the first scored document.
    metric_names: list[str] = []
    for doc in docs:
        scores = doc.eval.get("scores")
        if scores:
            metric_names = sorted(scores.keys())
            break

    # Per-document scores CSV.
    scores_path = eval_dir / "scores.csv"
    with open(scores_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["doc_id"] + metric_names)
        for doc in docs:
            doc_id = doc.input.get("doc_id", "unknown")
            scores = doc.eval.get("scores") or {}
            row = [doc_id] + [scores.get(m, "") for m in metric_names]
            writer.writerow(row)

    # Aggregate JSON.
    agg_path = eval_dir / "aggregates.json"
    with open(agg_path, "w", encoding="utf-8") as fh:
        json.dump(aggregate, fh, indent=2, ensure_ascii=False)
