# Config Format

Pipeline configurations are JSON files that fully specify a pipeline: which
components to run, in what order, and with what parameters. Configs are the
foundation for reproducibility in gmpp.

## Schema

```json
{
  "components": [
    {
      "name": "<registered_component_name>",
      "params": {
        "<param_name>": "<value>",
        ...
      }
    },
    ...
  ],
  "python_version": "3.12.x ...",
  "timestamp": "2026-02-15T10:30:00.000000"
}
```

## Fields

| Field             | Type             | Description                                      |
|-------------------|------------------|--------------------------------------------------|
| `components`      | `list[object]`   | Ordered list of component specifications.        |
| `components[].name`   | `str`       | Registered name of the component.                |
| `components[].params` | `object`    | Constructor parameters for the component.        |
| `python_version`  | `str`            | Python version used when the config was created. |
| `timestamp`       | `str`            | ISO 8601 timestamp of config creation.           |

## Annotated example

This config runs jusText with German stopwords followed by a trafilatura
extraction step. Note that both components write to `"text"`, so trafilatura
will overwrite the jusText output (gmpp will emit a warning):

```json
{
  "components": [
    {
      "name": "justext",
      "params": {
        "language": "German",
        "length_low": 70,
        "length_high": 200,
        "stopwords_low": 0.30,
        "stopwords_high": 0.32,
        "max_link_density": 0.2,
        "max_heading_distance": 200,
        "no_headings": false
      }
    },
    {
      "name": "trafilatura",
      "params": {
        "favor_precision": true,
        "favor_recall": false,
        "include_tables": true,
        "include_links": false,
        "include_images": false,
        "deduplicate": false,
        "no_fallback": false
      }
    }
  ],
  "python_version": "3.12.0 (main, Oct  2 2023, 00:00:00) [Clang 15.0.0]",
  "timestamp": "2026-02-15T10:30:00.000000"
}
```

## Generating a config from Python

You never need to write config files by hand. Generate them from a Pipeline:

```python
import json
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura

pipe = Pipeline([Trafilatura(favor_precision=True)])
config = pipe.to_config()

with open("config.json", "w") as f:
    json.dump(config, f, indent=2)
```

## Loading a config

```python
import json
from gmpp import Pipeline

with open("config.json") as f:
    config = json.load(f)

pipe = Pipeline.from_config(config)
```

The `from_config` method looks up each component name in the registry and
instantiates it with the saved parameters. If a component name is not
registered (e.g., the required library is not installed), it raises a
`KeyError` with a message listing the available components.

## CSV manifest format

The `load_corpus` function also accepts a CSV manifest as input. This is
not a pipeline config but a corpus description:

```csv
doc_id,path,url,ground_truth_path
page_001,htmls/page_001.html,https://example.com/page,gt/page_001.txt
page_002,htmls/page_002.html,,gt/page_002.txt
```

| Column              | Required | Description                                    |
|---------------------|----------|------------------------------------------------|
| `doc_id`            | Yes      | Unique identifier for the document.            |
| `path`              | Yes      | Path to the HTML file (relative to manifest).  |
| `url`               | No       | Original URL of the page.                      |
| `ground_truth_path` | No       | Path to ground truth text file.                |
