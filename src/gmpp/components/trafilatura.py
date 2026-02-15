"""Trafilatura component -- general-purpose web content extraction."""

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("trafilatura")
class Trafilatura(Component):
    """Wrapper around the trafilatura library for HTML content extraction.

    trafilatura is a general-purpose extractor with strong performance
    across diverse page types. It supports precision/recall trade-offs
    and optional extraction of tables, links, and images.
    """

    output_field = "text"

    def __init__(
        self,
        favor_precision: bool = True,
        favor_recall: bool = False,
        include_tables: bool = True,
        include_links: bool = False,
        include_images: bool = False,
        deduplicate: bool = False,
        no_fallback: bool = False,
    ) -> None:
        self.favor_precision = favor_precision
        self.favor_recall = favor_recall
        self.include_tables = include_tables
        self.include_links = include_links
        self.include_images = include_images
        self.deduplicate = deduplicate
        self.no_fallback = no_fallback

    def process(self, doc: Document) -> Document:
        try:
            import trafilatura
        except ImportError:
            raise ImportError(
                "trafilatura is required for the Trafilatura component. "
                "Install it with: pip install trafilatura"
            ) from None

        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            return doc

        result = trafilatura.extract(
            html,
            favor_precision=self.favor_precision,
            favor_recall=self.favor_recall,
            include_tables=self.include_tables,
            include_links=self.include_links,
            include_images=self.include_images,
            deduplicate=self.deduplicate,
            no_fallback=self.no_fallback,
        )
        doc.content[self.output_field] = result if result is not None else ""
        return doc
