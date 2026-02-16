"""Newspaper component -- article-focused extraction via newspaper4k."""

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("newspaper")
class Newspaper(Component):
    """Wrapper around newspaper4k for HTML content extraction.

    newspaper4k is an article-focused extractor that also pulls rich
    metadata (title, authors, publish date) from the page.
    """

    output_field = "text"

    def __init__(self, language: str = "en") -> None:
        self.language = language

    def process(self, doc: Document) -> Document:
        try:
            from newspaper import Article, Config
        except ImportError:
            raise ImportError(
                "newspaper4k is required for the Newspaper component. "
                "Install it with: pip install newspaper4k"
            ) from None

        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            return doc

        config = Config()
        config.fetch_images = False
        config.language = self.language

        url = doc.input.get("url", "")
        article = Article(
            url if url else "http://example.com",
            config=config,
        )
        article.download(input_html=html)
        # newspaper4k's parse() unconditionally calls fetch_images() which
        # triggers network requests regardless of config.fetch_images.
        # Monkey-patch it out to avoid slow/failing HTTP requests.
        article.fetch_images = lambda: None
        article.parse()

        doc.content[self.output_field] = article.text

        if article.title:
            doc.content.setdefault("title", article.title)
        if article.authors:
            doc.content.setdefault("authors", article.authors)
        if article.publish_date:
            doc.content.setdefault("publish_date", str(article.publish_date))

        return doc
