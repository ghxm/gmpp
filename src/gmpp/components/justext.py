"""JusText component -- linguistically principled boilerplate removal."""

from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("justext")
class JusText(Component):
    """Wrapper around the jusText library for HTML content extraction.

    jusText uses a linguistically motivated algorithm that classifies
    text blocks as boilerplate or content based on stopword density,
    link density, and text length thresholds.
    """

    output_field = "text"

    def __init__(
        self,
        language: str = "English",
        length_low: int = 70,
        length_high: int = 200,
        stopwords_low: float = 0.30,
        stopwords_high: float = 0.32,
        max_link_density: float = 0.2,
        max_heading_distance: int = 200,
        no_headings: bool = False,
    ) -> None:
        self.language = language
        self.length_low = length_low
        self.length_high = length_high
        self.stopwords_low = stopwords_low
        self.stopwords_high = stopwords_high
        self.max_link_density = max_link_density
        self.max_heading_distance = max_heading_distance
        self.no_headings = no_headings

    def process(self, doc: Document) -> Document:
        try:
            import justext
        except ImportError:
            raise ImportError(
                "jusText is required for the JusText component. "
                "Install it with: pip install jusText"
            ) from None

        html = doc.content.get("html", "")
        if not html:
            doc.content[self.output_field] = ""
            return doc

        stoplist = justext.get_stoplist(self.language)
        paragraphs = justext.justext(
            html,
            stoplist,
            length_low=self.length_low,
            length_high=self.length_high,
            stopwords_low=self.stopwords_low,
            stopwords_high=self.stopwords_high,
            max_link_density=self.max_link_density,
            max_heading_distance=self.max_heading_distance,
            no_headings=self.no_headings,
        )
        text_parts = [p.text for p in paragraphs if not p.is_boilerplate]
        doc.content[self.output_field] = "\n\n".join(text_parts)
        return doc
