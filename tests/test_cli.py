"""Tests for the gmpp CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from gmpp import Component
from gmpp.cli import cli
from gmpp.registry import register_component, _components


# -- Test component ------------------------------------------------------------


@register_component("test_upper")
class UpperCase(Component):
    """Test component that uppercases the HTML content."""

    output_field = "text"

    def process(self, doc):
        doc.content[self.output_field] = doc.content.get("html", "").upper()
        return doc


# -- Fixtures / helpers --------------------------------------------------------


def _make_config(tmp_path: Path) -> Path:
    """Create a minimal pipeline config using the test_upper component."""
    config = {
        "components": [{"name": "test_upper", "params": {}}],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _make_input_dir(tmp_path: Path) -> Path:
    """Create a directory with minimal HTML files."""
    input_dir = tmp_path / "htmls"
    input_dir.mkdir()
    (input_dir / "doc_a.html").write_text("<p>Hello world</p>", encoding="utf-8")
    (input_dir / "doc_b.html").write_text("<p>Foo bar</p>", encoding="utf-8")
    return input_dir


def _make_ground_truth(tmp_path: Path) -> Path:
    """Create ground-truth .txt files matching the test HTML docs."""
    gt_dir = tmp_path / "gt"
    gt_dir.mkdir()
    (gt_dir / "doc_a.txt").write_text("<P>HELLO WORLD</P>", encoding="utf-8")
    (gt_dir / "doc_b.txt").write_text("<P>FOO BAR</P>", encoding="utf-8")
    return gt_dir


def _run_pipeline(tmp_path: Path) -> Path:
    """Run the pipeline and return the output directory (for use in later tests)."""
    config_path = _make_config(tmp_path)
    input_dir = _make_input_dir(tmp_path)
    output_dir = tmp_path / "output"

    runner = CliRunner()
    result = runner.invoke(cli, [
        "run", str(config_path),
        "--input", str(input_dir),
        "--output", str(output_dir),
    ])
    assert result.exit_code == 0, result.output
    return output_dir


# -- Tests ---------------------------------------------------------------------


class TestList:
    def test_shows_registered_components(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Components:" in result.output
        assert "test_upper" in result.output

    def test_shows_registered_metrics(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Metrics:" in result.output
        # Built-in metrics should be listed after importing gmpp.eval.
        assert "token_f1" in result.output


class TestShow:
    def test_shows_pipeline_config(self, tmp_path: Path):
        config_path = _make_config(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["show", str(config_path)])
        assert result.exit_code == 0
        assert "1 component(s)" in result.output
        assert "test_upper" in result.output

    def test_invalid_config_missing_components(self, tmp_path: Path):
        bad_config = tmp_path / "bad.json"
        bad_config.write_text("{}", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, ["show", str(bad_config)])
        assert result.exit_code != 0
        assert "missing 'components'" in result.output

    def test_invalid_json(self, tmp_path: Path):
        bad_file = tmp_path / "broken.json"
        bad_file.write_text("not json!", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, ["show", str(bad_file)])
        assert result.exit_code != 0


class TestRun:
    def test_end_to_end(self, tmp_path: Path):
        config_path = _make_config(tmp_path)
        input_dir = _make_input_dir(tmp_path)
        output_dir = tmp_path / "output"

        runner = CliRunner()
        result = runner.invoke(cli, [
            "run", str(config_path),
            "--input", str(input_dir),
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0, result.output
        assert "Loaded 2 document(s)" in result.output
        assert "Processed 2 document(s)" in result.output
        assert (output_dir / "config.json").exists()
        assert (output_dir / "results" / "doc_a.json").exists()
        assert (output_dir / "results" / "doc_b.json").exists()

    def test_results_contain_uppercased_text(self, tmp_path: Path):
        output_dir = _run_pipeline(tmp_path)

        doc_a_path = output_dir / "results" / "doc_a.json"
        with open(doc_a_path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["content"]["text"] == "<P>HELLO WORLD</P>"

    def test_invalid_config(self, tmp_path: Path):
        bad_config = tmp_path / "bad.json"
        bad_config.write_text('{"components": [{"name": "nonexistent"}]}',
                              encoding="utf-8")
        input_dir = _make_input_dir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, [
            "run", str(bad_config),
            "--input", str(input_dir),
            "--output", str(tmp_path / "out"),
        ])
        assert result.exit_code != 0


class TestEval:
    def test_end_to_end(self, tmp_path: Path):
        output_dir = _run_pipeline(tmp_path)
        gt_dir = _make_ground_truth(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, [
            "eval", str(output_dir),
            "--ground-truth", str(gt_dir),
            "--metrics", "token_precision,token_recall,token_f1",
        ])

        assert result.exit_code == 0, result.output
        assert "Aggregate scores:" in result.output
        assert "token_f1" in result.output
        assert (output_dir / "eval" / "scores.csv").exists()
        assert (output_dir / "eval" / "aggregates.json").exists()

    def test_perfect_scores(self, tmp_path: Path):
        """Ground truth matches prediction exactly, so token metrics should be 1.0."""
        output_dir = _run_pipeline(tmp_path)
        gt_dir = _make_ground_truth(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, [
            "eval", str(output_dir),
            "--ground-truth", str(gt_dir),
            "--metrics", "token_f1",
        ])

        assert result.exit_code == 0, result.output
        # Load aggregates and check scores.
        agg_path = output_dir / "eval" / "aggregates.json"
        with open(agg_path, encoding="utf-8") as fh:
            agg = json.load(fh)
        assert agg["token_f1"]["mean"] == 1.0

    def test_no_results(self, tmp_path: Path):
        """Should fail gracefully when output dir has no results."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        (empty_dir / "results").mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["eval", str(empty_dir)])
        assert result.exit_code != 0


class TestInspect:
    def test_shows_provenance(self, tmp_path: Path):
        output_dir = _run_pipeline(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(output_dir)])

        assert result.exit_code == 0, result.output
        assert "Documents:" in result.output
        assert "2" in result.output
        assert "UpperCase" in result.output
        assert "Timing" in result.output

    def test_shows_config_info(self, tmp_path: Path):
        output_dir = _run_pipeline(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(output_dir)])

        assert result.exit_code == 0, result.output
        assert "Pipeline:" in result.output
        assert "test_upper" in result.output

    def test_no_results(self, tmp_path: Path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        (empty_dir / "results").mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(empty_dir)])
        assert result.exit_code != 0
