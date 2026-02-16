# Write a custom component

See [Component concepts](../concepts/component.md) for a detailed walkthrough.
The minimal version:

```python
from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component

@register_component("my_extractor")
class MyExtractor(Component):
    output_field = "text"

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def process(self, doc: Document) -> Document:
        html = doc.content.get("html", "")
        # Your extraction logic here
        doc.content[self.output_field] = extracted_text
        return doc
```

Requirements:

1. Subclass `Component`.
2. Set `output_field`.
3. Implement `process(doc)` -- read from `doc.content`, write to `doc.content[self.output_field]`.
4. Store constructor parameters as instance attributes (for `get_params()` introspection).
5. Decorate with `@register_component("name")` if you want config serialization.
