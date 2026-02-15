"""Readability component -- article extraction via readability-lxml."""

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("readability")
class Readability(Component):
    """Wrapper around readability-lxml for HTML content extraction.

    readability-lxml extracts the main article content from a page,
    producing a cleaned HTML summary that is then converted to plain text.
    """

    output_field = "text"

    def __init__(
        self,
        min_text_length: int = 25,
        retry_length: int = 250,
    ) -> None:
        self.min_text_length = min_text_length
        self.retry_length = retry_length

    def process(self, doc: Document) -> Document:
        try:
            from readability import Document as ReadabilityDocument
        except ImportError:
            raise ImportError(
                "readability-lxml is required for the Readability component. "
                "Install it with: pip install readability-lxml"
            ) from None

        try:
            import lxml.html
        except ImportError:
            raise ImportError(
                "lxml is required for the Readability component. "
                "Install it with: pip install lxml"
            ) from None

        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            return doc

        readable = ReadabilityDocument(
            html,
            min_text_length=self.min_text_length,
            retry_length=self.retry_length,
        )
        summary_html = readable.summary()

        tree = lxml.html.fromstring(summary_html)
        text = tree.text_content()
        doc.content[self.output_field] = text.strip()
        return doc
