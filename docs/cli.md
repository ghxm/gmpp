# CLI Reference

gmpp provides a command-line interface for running pipelines and evaluating
results without writing Python code. The CLI is built with Click and installed
as the `gmpp` command.

!!! note
    The CLI module (`gmpp.cli`) is defined in `pyproject.toml` but may not
    yet be fully implemented. The commands below reflect the planned interface
    from the architecture specification.

## gmpp run

Run a pipeline defined in a JSON config on a corpus of HTML files.

```bash
gmpp run <config.json> --input <dir|manifest.csv> --output <dir> [--parallelism N]
```

| Option          | Required | Description                                         |
|-----------------|----------|-----------------------------------------------------|
| `config.json`   | Yes      | Path to the pipeline config file.                   |
| `--input`       | Yes      | Directory of `.html` files or a CSV manifest.       |
| `--output`      | Yes      | Output directory for results and config sidecar.    |
| `--parallelism` | No       | Number of parallel workers (default: 1).            |

**Example**:

```bash
gmpp run config.json --input ./htmls/ --output ./results/
```

This creates the following output structure:

```
results/
  config.json              # copy of the pipeline config
  results/
    doc_001.json           # per-document results
    doc_002.json
    manifest.csv           # list of all doc_ids
```

## gmpp eval

Evaluate pipeline results against ground truth.

```bash
gmpp eval <output_dir> --ground-truth <dir|csv> [--metrics rouge_lsum,levenshtein]
```

| Option           | Required | Description                                        |
|------------------|----------|----------------------------------------------------|
| `output_dir`     | Yes      | Directory containing pipeline results.             |
| `--ground-truth` | Yes      | Directory of `.txt` ground truth files or CSV.     |
| `--metrics`      | No       | Comma-separated metric names (default: all).       |

**Example**:

```bash
gmpp eval ./results/ --ground-truth ./gt/ --metrics rouge_lsum,levenshtein
```

This creates:

```
results/
  eval/
    scores.csv             # per-document metric scores
    aggregates.json        # corpus-level statistics (mean, median, std)
```

## gmpp list

List all registered components and their parameters.

```bash
gmpp list
```

**Example output**:

```
Components:
  trafilatura    Trafilatura(favor_precision=True, favor_recall=False, ...)
  readability    Readability(min_text_length=25, retry_length=250)
  justext        JusText(language='English', length_low=70, ...)
  newspaper      Newspaper(language='en')
  inscriptis     Inscriptis(display_images=False, ...)
```

## gmpp show

Validate and pretty-print a pipeline config file.

```bash
gmpp show <config.json>
```

**Example**:

```bash
gmpp show config.json
```

Prints the config with component names, parameters, and metadata in a
human-readable format.

## gmpp inspect

Show provenance information for a completed pipeline run.

```bash
gmpp inspect <output_dir>
```

Shows what pipeline was used, when it ran, timing information per component,
and the Python version.

## Input formats

The `--input` argument accepts two formats:

**Directory**: A folder containing `.html` files. Each file becomes a Document
with `doc_id` set to the filename stem (e.g., `page_001.html` becomes
`doc_id = "page_001"`).

**CSV manifest**: A CSV file with at least `doc_id` and `path` columns.
Optional columns: `url`, `ground_truth_path`.

```csv
doc_id,path,url,ground_truth_path
page_001,htmls/page_001.html,https://example.com/page,gt/page_001.txt
page_002,htmls/page_002.html,,gt/page_002.txt
```

Paths in the manifest are relative to the manifest file's directory.
