# Pipeline

A Pipeline is an ordered list of Components that processes Documents. It handles
execution order, provenance tracking, and configuration serialization.

## Creating a pipeline

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura
from gmpp.components.readability import Readability

# Single-step pipeline
pipe = Pipeline([Trafilatura(favor_precision=True)])

# Multi-step pipeline
pipe = Pipeline([
    HtmlCleaner(),          # preprocessing
    Trafilatura(),          # extraction
])
```

## Running a single document

```python
from gmpp.document import Document

doc = Document(input={"html": "<html>...</html>", "doc_id": "page_001"})
result = pipe.run(doc)

print(result.content["text"])   # extracted text
print(result.history)           # list of StepRecords
```

`run()` passes the Document through each component in order. After each step,
a `StepRecord` is appended to `doc.history` recording the component name,
output field, timestamp, duration, and parameters.

## Running a corpus

```python
from gmpp.io import load_corpus

docs = load_corpus("./htmls/")
results = pipe.run_corpus(docs)
```

`run_corpus()` does two things that `run()` does not:

1. Calls `setup(corpus)` on each component before processing starts.
   This is needed for corpus-aware components like template induction.
2. Checks for field overwrites and emits a warning if two components
   write to the same `output_field`.

## Configuration serialization

Pipelines can be saved to and loaded from JSON configs. This is the foundation
for reproducibility: you can share a config file and someone else can
reconstruct the exact same pipeline.

### Saving a config

```python
import json

config = pipe.to_config()
with open("config.json", "w") as f:
    json.dump(config, f, indent=2)
```

The config includes:

- The list of components with their registered names and parameters.
- The Python version.
- A timestamp.

### Loading a config

```python
import json
from gmpp import Pipeline

with open("config.json") as f:
    config = json.load(f)

pipe = Pipeline.from_config(config)
```

This uses the registry to look up each component by name and instantiate it
with the saved parameters.

## Introspection

```python
# Number of components
len(pipe)

# Access a component by index
pipe[0]

# Display the pipeline
print(pipe)
# Pipeline([Trafilatura(favor_precision=True, ...)])
```
