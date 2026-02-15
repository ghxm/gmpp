"""Tests for gmpp.pipeline."""

from __future__ import annotations

import warnings

import pytest

from gmpp import Component, Document, Pipeline, register_component


# -- helper components local to this module -----------------------------------


@register_component("add_text")
class AddTextComponent(Component):
    """Writes a fixed string to doc.content['text']."""

    output_field = "text"

    def __init__(self, value: str = "hello") -> None:
        self.value = value

    def process(self, doc: Document) -> Document:
        doc.content["text"] = self.value
        return doc


@register_component("add_lang")
class AddLangComponent(Component):
    """Writes a fixed language tag to doc.content['lang']."""

    output_field = "lang"

    def __init__(self, lang: str = "en") -> None:
        self.lang = lang

    def process(self, doc: Document) -> Document:
        doc.content["lang"] = self.lang
        return doc

    def setup(self, corpus: list[Document]) -> None:
        # Mark that setup was called for test verification.
        self._setup_called = True


class TestPipelineRun:
    def test_components_run_in_order(self) -> None:
        doc = Document(input={"html": "<p>test</p>"})
        pipe = Pipeline([AddTextComponent(value="first"), AddTextComponent(value="second")])
        result = pipe.run(doc)
        # The last component wins because both write to "text".
        assert result.content["text"] == "second"

    def test_history_records_created(self) -> None:
        doc = Document(input={"html": "<p>test</p>"})
        pipe = Pipeline([AddTextComponent(), AddLangComponent()])
        result = pipe.run(doc)

        assert len(result.history) == 2
        assert result.history[0].component_name == "AddTextComponent"
        assert result.history[0].output_field == "text"
        assert result.history[1].component_name == "AddLangComponent"
        assert result.history[1].output_field == "lang"
        # Duration should be non-negative
        assert all(rec.duration_s >= 0 for rec in result.history)
        # Timestamps should be ISO format strings
        assert all(isinstance(rec.timestamp, str) for rec in result.history)


class TestPipelineCorpus:
    def test_run_corpus_calls_setup(self) -> None:
        lang_comp = AddLangComponent()
        pipe = Pipeline([AddTextComponent(), lang_comp])
        docs = [Document(input={"html": "<p>a</p>"})]
        pipe.run_corpus(docs)
        assert getattr(lang_comp, "_setup_called", False)

    def test_field_overwrite_warning(self) -> None:
        pipe = Pipeline([AddTextComponent(value="a"), AddTextComponent(value="b")])
        docs = [Document(input={"html": "<p>x</p>"})]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            pipe.run_corpus(docs)
        overwrite_warnings = [
            w for w in caught if "overwrites field" in str(w.message)
        ]
        assert len(overwrite_warnings) == 1


class TestPipelineSerialization:
    def test_to_config_from_config_round_trip(self) -> None:
        pipe = Pipeline([AddTextComponent(value="hi"), AddLangComponent(lang="de")])
        config = pipe.to_config()

        assert "components" in config
        assert "python_version" in config
        assert "timestamp" in config
        assert len(config["components"]) == 2

        reconstructed = Pipeline.from_config(config)
        assert len(reconstructed) == 2
        assert reconstructed[0].get_params() == {"value": "hi"}
        assert reconstructed[1].get_params() == {"lang": "de"}


class TestPipelineDunder:
    def test_len(self) -> None:
        pipe = Pipeline([AddTextComponent(), AddLangComponent()])
        assert len(pipe) == 2

    def test_getitem(self) -> None:
        comp_a = AddTextComponent()
        comp_b = AddLangComponent()
        pipe = Pipeline([comp_a, comp_b])
        assert pipe[0] is comp_a
        assert pipe[1] is comp_b

    def test_repr(self) -> None:
        pipe = Pipeline([AddTextComponent()])
        assert repr(pipe).startswith("Pipeline([")
