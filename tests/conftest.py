"""Shared test fixtures and helper components."""

from __future__ import annotations

import pytest

from gmpp import Document, Component, register_component


# -- helper component --------------------------------------------------------


@register_component("uppercase")
class UpperCaseComponent(Component):
    """Test component that uppercases doc.content['text']."""

    output_field = "text"

    def process(self, doc: Document) -> Document:
        doc.content["text"] = doc.content.get("text", "").upper()
        return doc


# -- fixtures ----------------------------------------------------------------


@pytest.fixture
def sample_html() -> str:
    return "<html><body><p>Hello, world!</p></body></html>"


@pytest.fixture
def sample_doc(sample_html: str) -> Document:
    return Document(input={"html": sample_html, "doc_id": "test_001"})
