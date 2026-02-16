"""Validate gmpp component wrappers against the WCEB benchmark.

Loads WCEB documents, runs each extractor through a gmpp Pipeline,
evaluates with ROUGE-LSum and Levenshtein, and compares against pre-computed
reference scores from Bevendorff et al. (SIGIR 2023).

Note: WCEB used older library versions; scores will differ. The goal is to
verify wrappers work correctly and produce scores in the right ballpark.

Usage:
    python run_wceb.py                  # full corpus (3,985 docs, slow)
    python run_wceb.py --sample 500     # stratified sample (faster)
"""

import json
import logging
import random
import statistics
import sys
import time
import warnings
from pathlib import Path

# Suppress noisy warnings from newspaper4k (image fetching) and urllib3
logging.getLogger("newspaper").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*image.*", module="newspaper")

# Ensure the gmpp package is importable from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gmpp.document import Document
from gmpp.pipeline import Pipeline
from gmpp import create_component
from gmpp.eval import evaluate
import gmpp.components  # noqa: F401 -- trigger registration

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / "wceb" / "datasets" / "combined"
GT_DIR = DATA_DIR / "ground-truth"
HTML_DIR = DATA_DIR / "html"

DATASETS = [
    "cetd",
    "cleaneval",
    "cleanportaleval",
    "dragnet",
    "google-trends-2017",
    "l3s-gn1",
    "readability",
    "scrapinghub",
]

EXTRACTORS = ["trafilatura", "readability", "justext", "newspaper", "inscriptis"]

# WCEB reference scores (micro-averaged across all 3,985 docs)
REFERENCE = {
    "trafilatura": {"rouge_lsum": 0.8674, "levenshtein": 0.8627},
    "readability": {"rouge_lsum": 0.8548, "levenshtein": 0.8512},
    "justext":     {"rouge_lsum": 0.8056, "levenshtein": 0.8007},
    "newspaper":   {"rouge_lsum": 0.7994, "levenshtein": 0.7926},
    "inscriptis":  {"rouge_lsum": 0.6867, "levenshtein": 0.6822},
}

TOLERANCE = 0.10  # acceptable deviation from reference (ROUGE-LSum)
# Note: Levenshtein scores for inscriptis deviate more because inscriptis
# preserves visual layout (extra whitespace), and Levenshtein is char-level.
# ROUGE-LSum (tokenized) is the primary validation metric.

# ---------------------------------------------------------------------------
# Load WCEB corpus
# ---------------------------------------------------------------------------


def load_wceb_corpus(sample_size: int | None = None) -> list[Document]:
    """Load WCEB documents across all datasets.

    If sample_size is given, take a stratified random sample (proportional
    to dataset size) for faster validation runs.
    """
    docs_by_dataset: dict[str, list[Document]] = {ds: [] for ds in DATASETS}

    for dataset in DATASETS:
        gt_file = GT_DIR / f"{dataset}.jsonl"
        html_dir = HTML_DIR / dataset
        with open(gt_file, encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                html_file = html_dir / f"{entry['page_id']}.html"
                if not html_file.exists():
                    continue
                html = html_file.read_text(encoding="utf-8", errors="replace")
                doc = Document(input={
                    "html": html,
                    "url": entry.get("url", ""),
                    "doc_id": entry["page_id"],
                    "dataset": dataset,
                })
                doc.eval["ground_truth"] = entry["plaintext"]
                docs_by_dataset[dataset].append(doc)

    if sample_size is None:
        docs = []
        for ds_docs in docs_by_dataset.values():
            docs.extend(ds_docs)
        return docs

    # Stratified sampling: proportional to dataset size
    total = sum(len(v) for v in docs_by_dataset.values())
    docs = []
    rng = random.Random(42)
    for dataset, ds_docs in docs_by_dataset.items():
        n = max(1, round(sample_size * len(ds_docs) / total))
        sampled = rng.sample(ds_docs, min(n, len(ds_docs)))
        docs.extend(sampled)

    return docs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def log(msg: str) -> None:
    """Print with immediate flush for unbuffered progress tracking."""
    print(msg, flush=True)


def main() -> None:
    # Parse --sample argument
    sample_size = None
    if "--sample" in sys.argv:
        idx = sys.argv.index("--sample")
        sample_size = int(sys.argv[idx + 1])

    log("Loading WCEB corpus...")
    docs = load_wceb_corpus(sample_size=sample_size)
    log(f"Loaded {len(docs)} documents from {len(DATASETS)} datasets.")
    if sample_size:
        log(f"(stratified sample of {sample_size} requested)\n")
    else:
        log("")

    results = {}
    for name in EXTRACTORS:
        log(f"Running {name}...")
        component = create_component(name)
        pipeline = Pipeline([component])

        # Deep-copy documents so each extractor starts fresh
        corpus = []
        for d in docs:
            fresh = Document(input=dict(d.input))
            fresh.eval["ground_truth"] = d.eval["ground_truth"]
            corpus.append(fresh)

        processed = pipeline.run_corpus(corpus)
        log(f"  Extraction done. Evaluating ({len(processed)} docs)...")

        # Evaluate per-doc with progress tracking (ROUGE is slow)
        eval_start = time.time()
        progress_interval = max(100, len(processed) // 10)
        for i, d in enumerate(processed):
            evaluate(d, metrics=["rouge_lsum", "levenshtein"])
            if (i + 1) % progress_interval == 0:
                elapsed = time.time() - eval_start
                log(f"    ... {i + 1}/{len(processed)} evaluated ({elapsed:.0f}s)")

        # Aggregate
        rouge_vals = [d.eval["scores"]["rouge_lsum"] for d in processed]
        lev_vals = [d.eval["scores"]["levenshtein"] for d in processed]
        empty_count = sum(
            1 for d in processed if not (d.content.get("text") or "").strip()
        )
        results[name] = {
            "rouge_lsum_mean": statistics.mean(rouge_vals),
            "rouge_lsum_median": statistics.median(rouge_vals),
            "levenshtein_mean": statistics.mean(lev_vals),
            "levenshtein_median": statistics.median(lev_vals),
            "empty_count": empty_count,
        }
        elapsed = time.time() - eval_start
        log(
            f"  ROUGE-LSum mean={results[name]['rouge_lsum_mean']:.4f}  "
            f"median={results[name]['rouge_lsum_median']:.4f}  "
            f"Levenshtein mean={results[name]['levenshtein_mean']:.4f}  "
            f"median={results[name]['levenshtein_median']:.4f}  "
            f"empty={empty_count}  ({elapsed:.0f}s)"
        )

    # --- Comparison table ---
    log("\n" + "=" * 90)
    log("COMPARISON: gmpp vs WCEB reference")
    log("=" * 90)
    header = (
        f"{'Extractor':<14} {'ROUGE ours':>10} {'ROUGE ref':>10} {'delta':>7} "
        f"{'Lev ours':>9} {'Lev ref':>9} {'delta':>7} {'Status':>8}"
    )
    log(header)
    log("-" * 90)

    all_pass = True
    ranking_ours = []
    for name in EXTRACTORS:
        r = results[name]
        ref = REFERENCE[name]
        rouge_delta = r["rouge_lsum_mean"] - ref["rouge_lsum"]
        lev_delta = r["levenshtein_mean"] - ref["levenshtein"]
        rouge_ok = abs(rouge_delta) <= TOLERANCE
        lev_ok = abs(lev_delta) <= TOLERANCE
        status = "PASS" if (rouge_ok and lev_ok) else "FAIL"
        if status == "FAIL":
            all_pass = False
        log(
            f"{name:<14} {r['rouge_lsum_mean']:>10.4f} {ref['rouge_lsum']:>10.4f} "
            f"{rouge_delta:>+7.4f} {r['levenshtein_mean']:>9.4f} "
            f"{ref['levenshtein']:>9.4f} {lev_delta:>+7.4f} {status:>8}"
        )
        ranking_ours.append((name, r["rouge_lsum_mean"]))

    # --- Ranking check ---
    ranking_ours.sort(key=lambda x: x[1], reverse=True)
    ranking_ref = sorted(REFERENCE.items(), key=lambda x: x[1]["rouge_lsum"], reverse=True)
    ours_order = [name for name, _ in ranking_ours]
    ref_order = [name for name, _ in ranking_ref]

    log(f"\nRanking (ours):     {' > '.join(ours_order)}")
    log(f"Ranking (reference): {' > '.join(ref_order)}")
    ranking_match = ours_order == ref_order
    log(f"Ranking preserved:   {'YES' if ranking_match else 'NO'}")

    # --- Empty output check ---
    log("\nEmpty outputs:")
    for name in EXTRACTORS:
        count = results[name]["empty_count"]
        log(f"  {name}: {count}")

    # --- Summary ---
    log(f"\n{'=' * 90}")
    if all_pass:
        log("RESULT: ALL EXTRACTORS PASS (within +/- {:.0f}% tolerance)".format(
            TOLERANCE * 100
        ))
    else:
        log("RESULT: SOME EXTRACTORS OUTSIDE TOLERANCE")
    log("=" * 90)


if __name__ == "__main__":
    main()
