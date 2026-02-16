# gmpp

**Python package for comparing HTML parsing strategies.**

gmpp wraps different HTML-to-text parsers (trafilatura, readability, jusText,
newspaper4k, inscriptis) in a common pipeline interface. You build pipelines
from components, run them on corpora of HTML pages, and evaluate the results
against ground truth using standardized metrics.

## Who is this for?

gmpp is built for researchers who need to systematically compare how different
text extraction tools perform on web content. If you are running a content
analysis study and need to decide which parser to use, or need to document
that your extraction pipeline is reproducible, gmpp gives you the scaffolding
to do that.

## Key features

- **Common interface** for multiple parser libraries.
- **Pipeline chaining**: combine preprocessing, extraction, and postprocessing steps.
- **Built-in evaluation** against ground truth (ROUGE-LSum, Levenshtein, token-level metrics).
- **Config serialization**: save and reload entire pipeline configurations as JSON.
- **CLI** for batch processing without writing Python code.

## Next steps

- [Getting Started](getting-started.md) -- install gmpp and run your first pipeline.
- [Concepts](concepts/document.md) -- understand how Documents, Components, and Pipelines work.
- [Cookbook](cookbook.md) -- recipes for common tasks.
