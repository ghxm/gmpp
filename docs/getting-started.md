# Getting Started

## Installation

Install gmpp with pip:

```bash
pip install gmpp
```

gmpp itself only depends on `click`. Parser backends and evaluation metrics are
optional dependencies. Install what you need:

```bash
# Individual backends
pip install "gmpp[trafilatura]"
pip install "gmpp[readability]"
pip install "gmpp[justext]"
pip install "gmpp[newspaper]"
pip install "gmpp[inscriptis]"

# Evaluation metrics (ROUGE, Levenshtein)
pip install "gmpp[eval]"

# Everything
pip install "gmpp[all]"

# Development (all backends + eval + pytest + ruff)
pip install "gmpp[dev]"
```

## Your first pipeline

A pipeline is an ordered list of components. Each component reads from a
Document, processes it, and writes the result back.

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.document import Document

# Create a Document from raw HTML
doc = Document(input={
    "html": "<html><body><p>Hello, world!</p></body></html>",
    "doc_id": "example_001",
})

# Build a single-step pipeline
pipe = Pipeline([Trafilatura(favor_precision=True)])

# Run it
result = pipe.run(doc)
print(result.content["text"])
```

The extracted text is stored in `doc.content["text"]` because Trafilatura's
`output_field` is `"text"`.

## Processing a corpus

To process many documents at once, use `load_corpus` and `run_corpus`:

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.io import load_corpus, save_results

# Load all .html files from a directory
docs = load_corpus("./htmls/")

# Run the pipeline on the full corpus
pipe = Pipeline([Trafilatura()])
results = pipe.run_corpus(docs)

# Save results to disk
save_results(results, "./output/", config=pipe.to_config())
```

`load_corpus` accepts either a directory of `.html` files or a CSV manifest
(see [Config Format](config.md) for manifest details).

## Evaluating results

If you have ground truth text, you can score extraction quality:

```python
from gmpp.io import load_corpus
from gmpp.eval import evaluate_corpus

# Load corpus with ground truth (matched by doc_id)
docs = load_corpus("./htmls/", ground_truth="./gt/")

# Run your pipeline (as above)
pipe = Pipeline([Trafilatura()])
results = pipe.run_corpus(docs)

# Score against ground truth
scores = evaluate_corpus(results, metrics=["rouge_lsum", "levenshtein"])

# Per-document scores
for entry in scores["per_doc"]:
    print(entry["doc_id"], entry["scores"])

# Corpus-level aggregates (mean, median, std)
for metric, stats in scores["aggregate"].items():
    print(f"{metric}: mean={stats['mean']:.3f}, median={stats['median']:.3f}")
```

Ground truth files are `.txt` files in the `--ground-truth` directory, matched
to HTML files by filename stem (e.g., `doc_001.html` matches `doc_001.txt`).

## Using the CLI

You can also run pipelines from the command line using a JSON config file:

```bash
# Run a pipeline
gmpp run config.json --input ./htmls/ --output ./results/

# Evaluate results
gmpp eval ./results/ --ground-truth ./gt/

# List available components
gmpp list
```

See [CLI Reference](cli.md) for all commands and options.
