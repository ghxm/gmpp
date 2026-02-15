"""Tests for gmpp.document."""

from __future__ import annotations

import types

import pytest

from gmpp.document import Document, StepRecord


class TestDocumentCreation:
    def test_input_is_frozen(self, sample_doc: Document) -> None:
        assert isinstance(sample_doc.input, types.MappingProxyType)
        with pytest.raises(TypeError):
            sample_doc.input["html"] = "modified"  # type: ignore[index]

    def test_content_is_mutable(self, sample_doc: Document) -> None:
        sample_doc.content["text"] = "extracted text"
        assert sample_doc.content["text"] == "extracted text"

    def test_content_initialized_from_input(self, sample_html: str) -> None:
        doc = Document(input={"html": sample_html})
        assert doc.content["html"] == sample_html

    def test_eval_defaults(self, sample_doc: Document) -> None:
        assert sample_doc.eval == {"ground_truth": None, "scores": None}

    def test_history_starts_empty(self, sample_doc: Document) -> None:
        assert sample_doc.history == []


class TestDocumentSerialization:
    def test_to_dict_round_trip(self, sample_doc: Document) -> None:
        sample_doc.history.append(
            StepRecord(
                component_name="test",
                output_field="text",
                timestamp="2026-01-01T00:00:00",
                duration_s=0.01,
                params={"k": "v"},
            )
        )
        data = sample_doc.to_dict()

        # input should be a plain dict in the serialized form
        assert isinstance(data["input"], dict)

        reconstructed = Document.from_dict(data)
        assert dict(reconstructed.input) == dict(sample_doc.input)
        assert reconstructed.content == sample_doc.content
        assert reconstructed.eval == sample_doc.eval
        assert reconstructed.history == sample_doc.history

    def test_from_dict_defaults(self) -> None:
        data = {"input": {"html": "<p>hi</p>"}}
        doc = Document.from_dict(data)
        assert doc.eval == {"ground_truth": None, "scores": None}
        assert doc.history == []
