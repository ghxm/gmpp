"""Tests for gmpp.io — corpus loading, result saving/loading, and eval output."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from gmpp.document import Document
from gmpp.io import load_corpus, load_results, save_eval, save_results


# -- load_corpus from directory ------------------------------------------------


class TestLoadCorpusFromDirectory:
    def test_loads_html_files(self, tmp_path: Path):
        (tmp_path / "doc_a.html").write_text("<p>Hello A</p>", encoding="utf-8")
        (tmp_path / "doc_b.html").write_text("<p>Hello B</p>", encoding="utf-8")

        docs = load_corpus(tmp_path)

        assert len(docs) == 2
        # Sorted by doc_id.
        assert docs[0].input["doc_id"] == "doc_a"
        assert docs[1].input["doc_id"] == "doc_b"
        assert docs[0].input["html"] == "<p>Hello A</p>"

    def test_ignores_non_html(self, tmp_path: Path):
        (tmp_path / "doc.html").write_text("<p>yes</p>", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("no", encoding="utf-8")

        docs = load_corpus(tmp_path)
        assert len(docs) == 1

    def test_url_is_none(self, tmp_path: Path):
        (tmp_path / "page.html").write_text("<p>x</p>", encoding="utf-8")

        docs = load_corpus(tmp_path)
        assert docs[0].input["url"] is None


# -- load_corpus from CSV manifest --------------------------------------------


class TestLoadCorpusFromManifest:
    def test_basic_manifest(self, tmp_path: Path):
        html_dir = tmp_path / "htmls"
        html_dir.mkdir()
        (html_dir / "page1.html").write_text("<h1>Page 1</h1>", encoding="utf-8")
        (html_dir / "page2.html").write_text("<h1>Page 2</h1>", encoding="utf-8")

        manifest = tmp_path / "manifest.csv"
        manifest.write_text(
            "doc_id,path,url\n"
            "page1,htmls/page1.html,http://example.com/1\n"
            "page2,htmls/page2.html,http://example.com/2\n",
            encoding="utf-8",
        )

        docs = load_corpus(manifest)

        assert len(docs) == 2
        assert docs[0].input["doc_id"] == "page1"
        assert docs[0].input["url"] == "http://example.com/1"
        assert docs[0].input["html"] == "<h1>Page 1</h1>"

    def test_manifest_with_ground_truth(self, tmp_path: Path):
        html_dir = tmp_path / "htmls"
        html_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()

        (html_dir / "page.html").write_text("<p>text</p>", encoding="utf-8")
        (gt_dir / "page.txt").write_text("ground truth text", encoding="utf-8")

        manifest = tmp_path / "manifest.csv"
        manifest.write_text(
            "doc_id,path,ground_truth_path\n"
            "page,htmls/page.html,gt/page.txt\n",
            encoding="utf-8",
        )

        docs = load_corpus(manifest)
        assert docs[0].eval["ground_truth"] == "ground truth text"


# -- Ground truth from directory -----------------------------------------------


class TestGroundTruthFromDirectory:
    def test_attaches_ground_truth(self, tmp_path: Path):
        html_dir = tmp_path / "htmls"
        html_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()

        (html_dir / "doc1.html").write_text("<p>html</p>", encoding="utf-8")
        (gt_dir / "doc1.txt").write_text("reference text", encoding="utf-8")

        docs = load_corpus(html_dir, ground_truth=gt_dir)
        assert docs[0].eval["ground_truth"] == "reference text"

    def test_missing_ground_truth_stays_none(self, tmp_path: Path):
        html_dir = tmp_path / "htmls"
        html_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()

        (html_dir / "doc1.html").write_text("<p>html</p>", encoding="utf-8")
        # No corresponding .txt in gt_dir.

        docs = load_corpus(html_dir, ground_truth=gt_dir)
        assert docs[0].eval["ground_truth"] is None


# -- save_results / load_results round-trip ------------------------------------


class TestSaveLoadResults:
    def test_round_trip(self, tmp_path: Path):
        docs = [
            Document(input={"doc_id": "a", "html": "<p>A</p>", "url": None}),
            Document(input={"doc_id": "b", "html": "<p>B</p>", "url": None}),
        ]
        docs[0].content["text"] = "extracted A"
        docs[1].content["text"] = "extracted B"

        output_dir = tmp_path / "output"
        save_results(docs, output_dir, config={"pipeline": "test"})

        # Verify files exist.
        assert (output_dir / "results" / "a.json").exists()
        assert (output_dir / "results" / "b.json").exists()
        assert (output_dir / "results" / "manifest.csv").exists()
        assert (output_dir / "config.json").exists()

        # Round-trip.
        loaded = load_results(output_dir)
        assert len(loaded) == 2
        assert loaded[0].input["doc_id"] == "a"
        assert loaded[1].input["doc_id"] == "b"
        assert loaded[0].content["text"] == "extracted A"

    def test_manifest_contents(self, tmp_path: Path):
        docs = [Document(input={"doc_id": "x", "html": "", "url": None})]
        output_dir = tmp_path / "out"
        save_results(docs, output_dir)

        manifest = output_dir / "results" / "manifest.csv"
        with open(manifest, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["doc_id"] == "x"

    def test_no_config_when_none(self, tmp_path: Path):
        docs = [Document(input={"doc_id": "z", "html": "", "url": None})]
        output_dir = tmp_path / "out"
        save_results(docs, output_dir, config=None)
        assert not (output_dir / "config.json").exists()


# -- save_eval -----------------------------------------------------------------


class TestSaveEval:
    def test_creates_files(self, tmp_path: Path):
        docs = [
            Document(input={"doc_id": "a", "html": "", "url": None}),
            Document(input={"doc_id": "b", "html": "", "url": None}),
        ]
        docs[0].eval["scores"] = {"token_f1": 0.9, "token_precision": 0.85}
        docs[1].eval["scores"] = {"token_f1": 0.7, "token_precision": 0.65}

        aggregate = {
            "token_f1": {"mean": 0.8, "median": 0.8, "std": 0.1},
            "token_precision": {"mean": 0.75, "median": 0.75, "std": 0.1},
        }

        output_dir = tmp_path / "output"
        save_eval(docs, output_dir, aggregate)

        # Check scores CSV.
        scores_path = output_dir / "eval" / "scores.csv"
        assert scores_path.exists()
        with open(scores_path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["doc_id"] == "a"
        assert "token_f1" in rows[0]
        assert float(rows[0]["token_f1"]) == pytest.approx(0.9)

        # Check aggregates JSON.
        agg_path = output_dir / "eval" / "aggregates.json"
        assert agg_path.exists()
        with open(agg_path, encoding="utf-8") as fh:
            loaded_agg = json.load(fh)
        assert loaded_agg["token_f1"]["mean"] == pytest.approx(0.8)
