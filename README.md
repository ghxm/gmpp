# gmpp

Python package for comparing HTML parsing strategies.
Wrap different parsers (e.g., the built-in trafilatura, readability, jusText, newspaper4k, inscriptis parsers)
in a common pipeline interface with built-in evaluation against ground truth.


## Install

```bash
pip install "gmpp @ git+https://github.com/ghxm/gmpp.git"
```

Install with specific parser backends:

```bash
pip install "gmpp[trafilatura] @ git+https://github.com/ghxm/gmpp.git"
pip install "gmpp[all] @ git+https://github.com/ghxm/gmpp.git"
pip install "gmpp[dev] @ git+https://github.com/ghxm/gmpp.git"
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

Full documentation: [https://ghxm.github.io/gmpp/](https://ghxm.github.io/gmpp/)

## License

MIT
