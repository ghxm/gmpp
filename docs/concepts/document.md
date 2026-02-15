# Document

The `Document` is the data container that flows through a pipeline. It carries
the original input, mutable working state, evaluation data, and a processing
history. Components read from it and write back to it.

## Structure

A Document has four parts:

| Attribute   | Type                           | Purpose                                    |
|-------------|--------------------------------|--------------------------------------------|
| `input`     | `MappingProxyType` (read-only) | Original data. Frozen after creation.      |
| `content`   | `dict`                         | Mutable working state. Components read/write here. |
| `eval`      | `dict`                         | Ground truth and computed scores.          |
| `history`   | `list[StepRecord]`             | Ordered log of processing steps.           |

### input (frozen)

`doc.input` is a read-only snapshot of the original data. It is set when the
Document is created and never modified by any component. This means you can
always access the original HTML, even after multiple processing steps have
transformed `doc.content`.

Common keys: `"html"`, `"doc_id"`, `"url"`.

### content (mutable)

`doc.content` is the working state. It is initialized as a mutable copy of
`doc.input`. Components read what they need from `content` and write their
results to their declared `output_field`.

For example, a Trafilatura component with `output_field = "text"` reads
`doc.content["html"]` and writes the extracted text to `doc.content["text"]`.

### eval

`doc.eval` holds evaluation-related data:

- `doc.eval["ground_truth"]`: the reference text (set by `load_corpus` or manually).
- `doc.eval["scores"]`: a dict of metric scores (populated by `evaluate()`).

### history

`doc.history` is a list of `StepRecord` named tuples. Each record logs which
component ran, what field it wrote to, when it ran, how long it took, and
what parameters it used. The pipeline populates this automatically.

## Creating a Document

```python
from gmpp.document import Document

doc = Document(input={
    "html": "<html><body><p>Article text here.</p></body></html>",
    "doc_id": "article_001",
    "url": "https://example.com/article",
})

# input is frozen (read-only)
print(doc.input["html"])       # works
# doc.input["html"] = "new"   # raises TypeError

# content starts as a mutable copy of input
print(doc.content["html"])     # same HTML
doc.content["text"] = "Article text here."  # components do this
```

## Loading Documents from files

In practice, you rarely create Documents by hand. Use `load_corpus`:

```python
from gmpp.io import load_corpus

# From a directory of .html files
docs = load_corpus("./htmls/")

# With ground truth
docs = load_corpus("./htmls/", ground_truth="./gt/")
```

## Serialization

Documents can be serialized to and from plain dicts (suitable for JSON):

```python
data = doc.to_dict()    # dict with input, content, eval, history
doc2 = Document.from_dict(data)
```

## StepRecord

Each entry in `doc.history` is a `StepRecord` with these fields:

| Field            | Type            | Description                         |
|------------------|-----------------|-------------------------------------|
| `component_name` | `str`           | Name of the component that ran.     |
| `output_field`   | `str`           | Which content key was written.      |
| `timestamp`      | `str`           | ISO 8601 timestamp.                 |
| `duration_s`     | `float`         | Processing time in seconds.         |
| `params`         | `dict[str, Any]`| Component parameters at runtime.    |
