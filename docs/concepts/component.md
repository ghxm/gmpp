# Component

A Component is one processing step in a pipeline. It wraps a specific library
or algorithm, reads from a Document, and writes its output to a declared field.

## Base class

All components inherit from `gmpp.component.Component`. The base class provides
parameter introspection, serialization, and a display method. You only need to
implement two things:

1. Set the `output_field` class attribute (the key in `doc.content` where results go).
2. Implement the `process(doc)` method.

## Interface

| Member            | Required? | Description                                              |
|-------------------|-----------|----------------------------------------------------------|
| `output_field`    | Yes       | Class attribute. Key in `doc.content` to write to.       |
| `process(doc)`    | Yes       | Process a single Document. Must return the Document.     |
| `setup(corpus)`   | No        | Called once before corpus processing (e.g., template induction). |
| `name`            | Inherited | Property returning the class name.                       |
| `get_params()`    | Inherited | Returns a dict of constructor parameters and values.     |
| `set_params()`    | Inherited | Sets attributes corresponding to constructor parameters. |
| `to_dict()`       | Inherited | Serializes to a config dict.                             |
| `from_dict()`     | Inherited | Reconstructs from a config dict via the registry.        |

## Writing a custom component

Here is a minimal example of a component that converts HTML to plain text
by stripping all tags:

```python
from gmpp.component import Component
from gmpp.document import Document
from gmpp.registry import register_component


@register_component("strip_tags")
class StripTags(Component):
    """Remove all HTML tags, keeping only text content."""

    output_field = "text"

    def __init__(self, separator: str = " ") -> None:
        self.separator = separator

    def process(self, doc: Document) -> Document:
        from html.parser import HTMLParser
        from io import StringIO

        class TagStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.result = StringIO()

            def handle_data(self, data):
                self.result.write(data)

        html = doc.content.get("html", "")
        stripper = TagStripper()
        stripper.feed(html)
        doc.content[self.output_field] = stripper.result.getvalue().strip()
        return doc
```

Key points:

- **`@register_component("strip_tags")`** makes this component available by name
  in configs and the registry.
- **`output_field = "text"`** declares that this component writes to `doc.content["text"]`.
- **Constructor parameters** become the component's configurable settings. The base
  class introspects them automatically via `get_params()`.
- **Lazy imports** inside `process()` keep gmpp importable even when the
  underlying library is not installed.

## Corpus-aware components

Some components need to see the entire corpus before processing individual
documents. For example, a template induction step might analyze all pages
from the same domain to identify shared boilerplate.

Override `setup(corpus)` for this:

```python
@register_component("template_inductor")
class TemplateInductor(Component):
    output_field = "cleaned_html"

    def setup(self, corpus: list[Document]) -> None:
        # Analyze the corpus to build templates
        self.templates = self._build_templates(corpus)

    def process(self, doc: Document) -> Document:
        html = doc.content.get("html", "")
        doc.content[self.output_field] = self._apply_template(html)
        return doc
```

`setup()` is called automatically by `Pipeline.run_corpus()` before any
documents are processed.

## In-place operations

A component can overwrite its input field. For example, an HTML cleaner
might read from and write to `"html"`:

```python
class HtmlCleaner(Component):
    output_field = "html"  # overwrites doc.content["html"]

    def process(self, doc: Document) -> Document:
        html = doc.content.get("html", "")
        doc.content[self.output_field] = clean(html)
        return doc
```

The original HTML is always preserved in `doc.input["html"]`.
