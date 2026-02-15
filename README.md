# gmpp

Lightweight framework for comparing HTML content extraction strategies.
Wrap different parsers (trafilatura, readability, jusText, newspaper4k, inscriptis)
in a common pipeline interface with built-in evaluation against ground truth.
Designed for computational social science researchers who need reproducible,
comparable text extraction from web pages.

## Install from Github

```bash
# TODO install from github
```

Install with specific parser backends:

```bash
# TODO install from github, pip not available yet
pip install "gmpp[trafilatura]"        # just trafilatura
pip install "gmpp[all]"                # all backends + eval metrics
pip install "gmpp[dev]"                # everything + pytest, ruff
```

## Quick start

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.io import load_corpus
from gmpp.eval import evaluate_corpus

# Load HTML files and ground truth
docs = load_corpus("./htmls/", ground_truth="./gt/")

# Build and run a pipeline
pipe = Pipeline([Trafilatura(favor_precision=True)])
results = pipe.run_corpus(docs)

# Evaluate against ground truth
scores = evaluate_corpus(results, metrics=["rouge_lsum", "levenshtein"])
print(scores["aggregate"])
```

## CLI

```bash
# Run a pipeline on a corpus
gmpp run config.json --input ./htmls/ --output ./results/

# Evaluate results against ground truth
gmpp eval ./results/ --ground-truth ./gt/

# List registered components
gmpp list

# Inspect a config file
gmpp show config.json
```

## Documentation

Full documentation: [https://ghxm.github.io/gmpp/](https://maxhaag.github.io/gmpp/)

## License

MIT
