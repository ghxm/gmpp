"""Tests for gmpp.eval — metrics, document-level, and corpus-level evaluation."""

from __future__ import annotations

import math

import pytest

from gmpp.document import Document
from gmpp.eval import (
    cosine,
    evaluate,
    evaluate_corpus,
    jaccard,
    levenshtein,
    rouge_lsum,
    token_f1,
    token_precision,
    token_recall,
)


# -- Individual metric tests --------------------------------------------------


class TestRougeSum:
    def test_identical_strings(self):
        score = rouge_lsum("the cat sat on the mat", "the cat sat on the mat")
        assert score == pytest.approx(1.0)

    def test_completely_different(self):
        score = rouge_lsum("alpha beta gamma", "one two three")
        assert score == pytest.approx(0.0)

    def test_partial_overlap(self):
        score = rouge_lsum("the cat sat", "the cat sat on the mat")
        assert 0.0 < score < 1.0


class TestLevenshtein:
    def test_identical(self):
        assert levenshtein("abc", "abc") == pytest.approx(1.0)

    def test_completely_different(self):
        score = levenshtein("aaa", "bbb")
        assert score == pytest.approx(0.0)

    def test_both_empty(self):
        assert levenshtein("", "") == pytest.approx(1.0)

    def test_one_empty(self):
        assert levenshtein("", "abc") == pytest.approx(0.0)
        assert levenshtein("abc", "") == pytest.approx(0.0)

    def test_partial(self):
        # "abc" vs "abd" -> distance 1, max_len 3 -> similarity 2/3
        assert levenshtein("abc", "abd") == pytest.approx(2.0 / 3.0)


class TestTokenPrecision:
    def test_perfect(self):
        assert token_precision("a b c", "a b c") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert token_precision("x y z", "a b c") == pytest.approx(0.0)

    def test_empty_predicted(self):
        assert token_precision("", "a b c") == pytest.approx(0.0)

    def test_partial(self):
        # predicted: "a b x", reference: "a b c" -> 2/3
        assert token_precision("a b x", "a b c") == pytest.approx(2.0 / 3.0)


class TestTokenRecall:
    def test_perfect(self):
        assert token_recall("a b c", "a b c") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert token_recall("x y z", "a b c") == pytest.approx(0.0)

    def test_empty_reference(self):
        assert token_recall("a b c", "") == pytest.approx(0.0)

    def test_empty_both(self):
        assert token_recall("", "") == pytest.approx(0.0)

    def test_partial(self):
        # predicted: "a b", reference: "a b c" -> 2/3
        assert token_recall("a b", "a b c") == pytest.approx(2.0 / 3.0)


class TestTokenF1:
    def test_perfect(self):
        assert token_f1("a b c", "a b c") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert token_f1("x y z", "a b c") == pytest.approx(0.0)

    def test_empty_both(self):
        assert token_f1("", "") == pytest.approx(0.0)

    def test_harmonic_mean(self):
        p = token_precision("a b x", "a b c")
        r = token_recall("a b x", "a b c")
        expected = 2 * p * r / (p + r)
        assert token_f1("a b x", "a b c") == pytest.approx(expected)


class TestJaccard:
    def test_identical(self):
        assert jaccard("a b c", "a b c") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert jaccard("x y z", "a b c") == pytest.approx(0.0)

    def test_both_empty(self):
        assert jaccard("", "") == pytest.approx(1.0)

    def test_one_empty(self):
        assert jaccard("", "a b c") == pytest.approx(0.0)
        assert jaccard("a b c", "") == pytest.approx(0.0)

    def test_partial(self):
        # predicted: "a b x", reference: "a b c"
        # intersection: {a, b}, union: {a, b, c, x} -> 2/4 = 0.5
        assert jaccard("a b x", "a b c") == pytest.approx(0.5)

    def test_duplicates_ignored(self):
        # set-based, so duplicates don't matter
        assert jaccard("a a b", "a b c") == pytest.approx(2.0 / 3.0)


class TestCosine:
    def test_identical(self):
        assert cosine("a b c", "a b c") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert cosine("x y z", "a b c") == pytest.approx(0.0)

    def test_both_empty(self):
        assert cosine("", "") == pytest.approx(1.0)

    def test_one_empty(self):
        assert cosine("", "a b c") == pytest.approx(0.0)
        assert cosine("a b c", "") == pytest.approx(0.0)

    def test_partial(self):
        # "a b" vs "a b c" -> dot=2, norm_pred=sqrt(2), norm_ref=sqrt(3)
        expected = 2 / (math.sqrt(2) * math.sqrt(3))
        assert cosine("a b", "a b c") == pytest.approx(expected)

    def test_frequency_sensitive(self):
        # "a a b" vs "a b b" -> counts: {a:2,b:1} vs {a:1,b:2}
        # dot = 2*1 + 1*2 = 4, norm_pred=sqrt(5), norm_ref=sqrt(5)
        expected = 4 / 5
        assert cosine("a a b", "a b b") == pytest.approx(expected)


# -- Document-level evaluation ------------------------------------------------


class TestEvaluate:
    def _make_doc(self, predicted: str, ground_truth: str) -> Document:
        doc = Document(input={"doc_id": "test", "html": ""})
        doc.content["text"] = predicted
        doc.eval["ground_truth"] = ground_truth
        return doc

    def test_basic(self):
        doc = self._make_doc("the cat sat", "the cat sat on the mat")
        result = evaluate(doc, metrics=["token_precision", "token_recall"])
        assert "token_precision" in result.eval["scores"]
        assert "token_recall" in result.eval["scores"]
        assert result is doc  # mutated in place

    def test_raises_without_ground_truth(self):
        doc = Document(input={"doc_id": "test", "html": ""})
        doc.content["text"] = "some text"
        with pytest.raises(ValueError, match="ground_truth"):
            evaluate(doc)

    def test_default_metrics_uses_all(self):
        doc = self._make_doc("hello world", "hello world")
        result = evaluate(doc)
        # All seven built-in metrics should be present.
        assert len(result.eval["scores"]) >= 7


# -- Corpus-level evaluation --------------------------------------------------


class TestEvaluateCorpus:
    def _make_doc(self, doc_id: str, predicted: str, ground_truth: str) -> Document:
        doc = Document(input={"doc_id": doc_id, "html": ""})
        doc.content["text"] = predicted
        doc.eval["ground_truth"] = ground_truth
        return doc

    def test_aggregation(self):
        docs = [
            self._make_doc("a", "hello world", "hello world"),
            self._make_doc("b", "foo bar", "foo bar baz"),
        ]
        result = evaluate_corpus(docs, metrics=["token_f1"])

        assert len(result["per_doc"]) == 2
        assert "token_f1" in result["aggregate"]
        agg = result["aggregate"]["token_f1"]
        assert "mean" in agg
        assert "median" in agg
        assert "std" in agg

    def test_per_doc_ids(self):
        docs = [
            self._make_doc("doc1", "x", "x"),
            self._make_doc("doc2", "y", "y"),
        ]
        result = evaluate_corpus(docs, metrics=["token_f1"])
        ids = [entry["doc_id"] for entry in result["per_doc"]]
        assert ids == ["doc1", "doc2"]

    def test_perfect_scores(self):
        docs = [
            self._make_doc("a", "same text", "same text"),
            self._make_doc("b", "same text", "same text"),
        ]
        result = evaluate_corpus(docs, metrics=["token_f1"])
        assert result["aggregate"]["token_f1"]["mean"] == pytest.approx(1.0)
        assert result["aggregate"]["token_f1"]["std"] == pytest.approx(0.0)
