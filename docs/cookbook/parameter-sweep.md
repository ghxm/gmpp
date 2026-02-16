# Run a parameter sweep (multiverse layer)

gmpp handles single-pipeline execution. A parameter sweep is an external loop
that creates multiple pipeline configs and runs each one. This allows for a "multiverse layer" over the core pipeline execution, where you can systematically explore different parameter combinations and compare their results.

## Python approach

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

## CLI approach

Generate config files for each parameter combination, then use a shell loop:

```bash
for config in configs/*.json; do
    name=$(basename "$config" .json)
    gmpp run "$config" --input ./htmls/ --output "./results/$name/"
    gmpp eval "./results/$name/" --ground-truth ./gt/
done
```

## Comparing across runs

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
