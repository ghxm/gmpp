# Components Reference

All built-in components extract text from HTML and write to `doc.content["text"]`
by default. Each wraps a different third-party library with different strengths.

## Overview

| Component      | Library          | Install extra    | Best for                              |
|----------------|------------------|------------------|---------------------------------------|
| `trafilatura`  | trafilatura      | `gmpp[trafilatura]` | General-purpose extraction         |
| `readability`  | readability-lxml | `gmpp[readability]` | Article-heavy pages                |
| `justext`      | jusText          | `gmpp[justext]`     | Linguistically principled removal  |
| `newspaper`    | newspaper4k      | `gmpp[newspaper]`   | News articles with metadata        |
| `inscriptis`   | inscriptis       | `gmpp[inscriptis]`  | Baseline (no boilerplate removal)  |

## Trafilatura

General-purpose web content extractor with strong performance across diverse
page types.

**Registered name**: `"trafilatura"`

| Parameter          | Type   | Default  | Description                                    |
|--------------------|--------|----------|------------------------------------------------|
| `favor_precision`  | `bool` | `True`   | Favor precision over recall.                   |
| `favor_recall`     | `bool` | `False`  | Favor recall over precision.                   |
| `include_tables`   | `bool` | `True`   | Include table content in output.               |
| `include_links`    | `bool` | `False`  | Include link targets in output.                |
| `include_images`   | `bool` | `False`  | Include image descriptions in output.          |
| `deduplicate`      | `bool` | `False`  | Remove duplicate paragraphs.                   |
| `no_fallback`      | `bool` | `False`  | Disable fallback extraction algorithms.        |

```python
from gmpp.components.trafilatura import Trafilatura

comp = Trafilatura(favor_precision=False, favor_recall=True)
```

## Readability

Extracts the main article content using readability-lxml, then converts the
cleaned HTML to plain text.

**Registered name**: `"readability"`

| Parameter          | Type  | Default | Description                                     |
|--------------------|-------|---------|-------------------------------------------------|
| `min_text_length`  | `int` | `25`    | Minimum text length for content blocks.         |
| `retry_length`     | `int` | `250`   | Retry threshold for shorter content.            |

```python
from gmpp.components.readability import Readability

comp = Readability(min_text_length=50)
```

## JusText

Linguistically motivated boilerplate removal. Classifies text blocks based on
stopword density, link density, and text length thresholds.

**Registered name**: `"justext"`

| Parameter               | Type    | Default    | Description                                     |
|-------------------------|---------|------------|-------------------------------------------------|
| `language`              | `str`   | `"English"`| Language for the stopword list.                 |
| `length_low`            | `int`   | `70`       | Short block threshold (characters).             |
| `length_high`           | `int`   | `200`      | Long block threshold (characters).              |
| `stopwords_low`         | `float` | `0.30`     | Low stopword density threshold.                 |
| `stopwords_high`        | `float` | `0.32`     | High stopword density threshold.                |
| `max_link_density`      | `float` | `0.2`      | Maximum link density for content blocks.        |
| `max_heading_distance`  | `int`   | `200`      | Max distance to nearest heading (characters).   |
| `no_headings`           | `bool`  | `False`    | Ignore headings in the classification.          |

```python
from gmpp.components.justext import JusText

comp = JusText(language="German", stopwords_high=0.35)
```

## Newspaper

Article-focused extractor via newspaper4k. Also extracts metadata like title,
authors, and publish date, which are stored as additional keys in `doc.content`.

**Registered name**: `"newspaper"`

| Parameter   | Type  | Default | Description                        |
|-------------|-------|---------|------------------------------------|
| `language`  | `str` | `"en"`  | Article language code.             |

Additional content keys set by this component (when available):

- `doc.content["title"]`
- `doc.content["authors"]`
- `doc.content["publish_date"]`

```python
from gmpp.components.newspaper import Newspaper

comp = Newspaper(language="en")
```

## Inscriptis

Converts HTML to plain text while preserving visual layout. Does not perform
boilerplate removal, making it useful as a baseline or for pages where all
content is relevant.

**Registered name**: `"inscriptis"`

| Parameter               | Type   | Default | Description                              |
|-------------------------|--------|---------|------------------------------------------|
| `display_images`        | `bool` | `False` | Include image alt text.                  |
| `display_links`         | `bool` | `False` | Include link targets.                    |
| `deduplicate_captions`  | `bool` | `False` | Remove duplicate captions.               |

```python
from gmpp.components.inscriptis import Inscriptis

comp = Inscriptis(display_links=True)
```
