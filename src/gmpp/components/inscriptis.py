"""Inscriptis component -- faithful HTML-to-text conversion (no boilerplate removal)."""

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("inscriptis")
class Inscriptis(Component):
    """Wrapper around inscriptis for HTML-to-text conversion.

    inscriptis converts HTML to plain text while preserving the visual
    layout. It does not perform boilerplate removal, making it useful
    as a baseline or for pages where all content is relevant.
    """

    output_field = "text"

    def __init__(
        self,
        display_images: bool = False,
        display_links: bool = False,
        deduplicate_captions: bool = False,
    ) -> None:
        self.display_images = display_images
        self.display_links = display_links
        self.deduplicate_captions = deduplicate_captions

    def process(self, doc: Document) -> Document:
        try:
            from inscriptis import get_text
            from inscriptis.model.config import ParserConfig
        except ImportError:
            raise ImportError(
                "inscriptis is required for the Inscriptis component. "
                "Install it with: pip install inscriptis"
            ) from None

        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            return doc

        config = ParserConfig(
            display_images=self.display_images,
            display_links=self.display_links,
            deduplicate_captions=self.deduplicate_captions,
        )
        text = get_text(html, config=config)
        doc.content[self.output_field] = text
        return doc
