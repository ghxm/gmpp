"""Click-based CLI for gmpp."""

import inspect
import json
import sys
from pathlib import Path

import click


@click.group()
def cli() -> None:
    """gmpp -- lightweight framework for comparing HTML content extraction strategies."""


# -- gmpp run -----------------------------------------------------------------


@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.option(
    "--input", "input_path", required=True, type=click.Path(exists=True),
    help="Input directory of .html files or CSV manifest.",
)
@click.option(
    "--output", "output_path", required=True, type=click.Path(),
    help="Output directory for results.",
)
def run(config: str, input_path: str, output_path: str) -> None:
    """Run a pipeline on a corpus.

    CONFIG is a JSON file describing the pipeline configuration.
    """
    from gmpp.io import load_corpus, save_results
    from gmpp.pipeline import Pipeline

    try:
        with open(config, encoding="utf-8") as fh:
            config_data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        click.echo(f"Error loading config: {exc}", err=True)
        sys.exit(1)

    try:
        pipe = Pipeline.from_config(config_data)
    except (KeyError, TypeError) as exc:
        click.echo(f"Error building pipeline from config: {exc}", err=True)
        sys.exit(1)

    docs = load_corpus(input_path)
    click.echo(f"Loaded {len(docs)} document(s) from {input_path}")

    component_names = [c.name for c in pipe.components]
    click.echo(f"Pipeline: {' -> '.join(component_names)}")

    results = pipe.run_corpus(docs)

    save_results(results, output_path, config=config_data)
    click.echo(f"Results saved to {output_path}")
    click.echo(f"Processed {len(results)} document(s) through {len(pipe)} component(s).")


# -- gmpp eval ----------------------------------------------------------------


@cli.command()
@click.argument("output_dir", type=click.Path(exists=True))
@click.option(
    "--ground-truth", "ground_truth", type=click.Path(exists=True), default=None,
    help="Directory of ground-truth .txt files (matched by doc_id).",
)
@click.option(
    "--metrics", "metrics_str", default=None,
    help="Comma-separated list of metrics to compute (default: all).",
)
def eval_cmd(output_dir: str, ground_truth: str | None, metrics_str: str | None) -> None:
    """Evaluate pipeline results against ground truth.

    OUTPUT_DIR is the directory produced by 'gmpp run'.
    """
    from gmpp.eval import evaluate_corpus
    from gmpp.io import _attach_ground_truth_from_dir, load_results, save_eval

    docs = load_results(output_dir)
    if not docs:
        click.echo("No results found in output directory.", err=True)
        sys.exit(1)

    click.echo(f"Loaded {len(docs)} document(s) from {output_dir}")

    # Attach ground truth if provided.
    if ground_truth is not None:
        gt_dir = Path(ground_truth)
        if gt_dir.is_dir():
            _attach_ground_truth_from_dir(docs, gt_dir)

    # Parse metrics option.
    metrics: list[str] | None = None
    if metrics_str is not None:
        metrics = [m.strip() for m in metrics_str.split(",") if m.strip()]

    try:
        results = evaluate_corpus(docs, metrics=metrics)
    except (ValueError, KeyError) as exc:
        click.echo(f"Evaluation error: {exc}", err=True)
        sys.exit(1)

    save_eval(docs, output_dir, results["aggregate"])
    click.echo(f"Evaluation saved to {Path(output_dir) / 'eval'}")

    # Print summary table.
    aggregate = results["aggregate"]
    if aggregate:
        click.echo("")
        click.echo("Aggregate scores:")
        # Header
        click.echo(f"  {'Metric':<20s} {'Mean':>8s} {'Median':>8s} {'Std':>8s}")
        click.echo(f"  {'-' * 20} {'-' * 8} {'-' * 8} {'-' * 8}")
        for metric_name, stats in sorted(aggregate.items()):
            click.echo(
                f"  {metric_name:<20s} "
                f"{stats['mean']:>8.4f} "
                f"{stats['median']:>8.4f} "
                f"{stats['std']:>8.4f}"
            )
    else:
        click.echo("No aggregate scores computed.")


# -- gmpp list ----------------------------------------------------------------


@cli.command("list")
def list_cmd() -> None:
    """List all registered components and metrics."""
    # Trigger component registration.
    import gmpp.components  # noqa: F401
    # Trigger metric registration.
    import gmpp.eval  # noqa: F401
    from gmpp.registry import list_components, list_metrics

    components = list_components()
    metrics = list_metrics()

    click.echo("Components:")
    if components:
        for name, cls in sorted(components.items()):
            try:
                sig = inspect.signature(cls.__init__)
                params = [
                    f"{p.name}={p.default!r}"
                    for p in sig.parameters.values()
                    if p.name != "self"
                    and p.kind not in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    )
                    and p.default is not inspect.Parameter.empty
                ]
                param_str = ", ".join(params)
            except (ValueError, TypeError, AttributeError):
                param_str = ""
            click.echo(f"  {name:<24s} {param_str}")
    else:
        click.echo("  (none registered)")

    click.echo("")
    click.echo("Metrics:")
    if metrics:
        for name in sorted(metrics):
            click.echo(f"  {name}")
    else:
        click.echo("  (none registered)")


# -- gmpp show ----------------------------------------------------------------


@cli.command()
@click.argument("config", type=click.Path(exists=True))
def show(config: str) -> None:
    """Validate and pretty-print a pipeline configuration.

    CONFIG is a JSON file describing the pipeline.
    """
    try:
        with open(config, encoding="utf-8") as fh:
            config_data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        click.echo(f"Error loading config: {exc}", err=True)
        sys.exit(1)

    if "components" not in config_data:
        click.echo("Invalid config: missing 'components' key.", err=True)
        sys.exit(1)

    components = config_data["components"]
    click.echo(f"Pipeline with {len(components)} component(s):")
    click.echo("")

    for i, comp in enumerate(components, 1):
        name = comp.get("name", "(unknown)")
        params = comp.get("params", {})
        click.echo(f"  {i}. {name}")
        if params:
            for key, value in params.items():
                click.echo(f"       {key}: {value!r}")

    # Show metadata if present.
    if "python_version" in config_data:
        click.echo("")
        click.echo(f"Python version: {config_data['python_version']}")
    if "timestamp" in config_data:
        click.echo(f"Timestamp:      {config_data['timestamp']}")


# -- gmpp inspect --------------------------------------------------------------


@cli.command()
@click.argument("output_dir", type=click.Path(exists=True))
def inspect(output_dir: str) -> None:
    """Inspect results directory: provenance, timing, and summary.

    OUTPUT_DIR is the directory produced by 'gmpp run'.
    """
    from gmpp.io import load_results

    output_path = Path(output_dir)

    # Load config if present.
    config_path = output_path / "config.json"
    config_data = None
    if config_path.exists():
        with open(config_path, encoding="utf-8") as fh:
            config_data = json.load(fh)

    docs = load_results(output_dir)
    if not docs:
        click.echo("No results found in output directory.", err=True)
        sys.exit(1)

    click.echo(f"Output directory: {output_path.resolve()}")
    click.echo(f"Documents:        {len(docs)}")

    # Show pipeline config summary.
    if config_data and "components" in config_data:
        components = config_data["components"]
        names = [c.get("name", "?") for c in components]
        click.echo(f"Pipeline:         {' -> '.join(names)}")
        if "timestamp" in config_data:
            click.echo(f"Config timestamp: {config_data['timestamp']}")

    # Compute timing stats from doc histories.
    timing: dict[str, list[float]] = {}
    for doc in docs:
        for step in doc.history:
            comp_name = step.component_name
            timing.setdefault(comp_name, []).append(step.duration_s)

    if timing:
        click.echo("")
        click.echo("Timing (seconds per document):")
        click.echo(f"  {'Component':<24s} {'Mean':>10s} {'Min':>10s} {'Max':>10s}")
        click.echo(f"  {'-' * 24} {'-' * 10} {'-' * 10} {'-' * 10}")
        for comp_name, durations in timing.items():
            mean_d = sum(durations) / len(durations)
            min_d = min(durations)
            max_d = max(durations)
            click.echo(
                f"  {comp_name:<24s} "
                f"{mean_d:>10.6f} "
                f"{min_d:>10.6f} "
                f"{max_d:>10.6f}"
            )
