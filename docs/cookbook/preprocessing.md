# Add a preprocessing step before extraction

If your HTML needs cleaning before extraction (e.g., removing navigation
elements, ads, or scripts), you can add a preprocessing component to the
pipeline. This component writes back to `"html"`, which the extractor then
reads from.

```python
from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component

@register_component("script_remover")
class ScriptRemover(Component):
    """Remove script and style tags from HTML."""

    output_field = "html"  # overwrites content["html"]

    def process(self, doc: Document) -> Document:
        import re

        html = doc.content.get("html", "")
        # Remove script and style blocks
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        doc.content[self.output_field] = html
        return doc


# Use it in a pipeline before the extractor
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura

pipe = Pipeline([
    ScriptRemover(),
    Trafilatura(favor_precision=True),
])
```

The original HTML is always preserved in `doc.input["html"]` regardless of
what preprocessing does to `doc.content["html"]`.
