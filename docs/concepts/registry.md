# Registry

The registry is a lookup table that maps string names to Component classes and
metric functions. It enables config-driven pipelines: a JSON config file
specifies component names and parameters, and the registry resolves those
names to actual Python classes at runtime.

## How it works

gmpp maintains two module-level dictionaries:

- `_components`: maps names like `"trafilatura"` to Component subclasses.
- `_metrics`: maps names like `"rouge_lsum"` to metric callables.

## Registering components

Use the `@register_component` decorator on a Component subclass:

```python
from gmpp.registry import register_component
from gmpp.component import Component

@register_component("my_parser")
class MyParser(Component):
    output_field = "text"

    def process(self, doc):
        # ...
        return doc
```

After this, `"my_parser"` can be used in JSON configs and with `create_component()`.

## Registering metrics

Use the `@register_metric` decorator on any callable with the signature
`(predicted: str, reference: str) -> float`:

```python
from gmpp.registry import register_metric

@register_metric("word_count_ratio")
def word_count_ratio(predicted: str, reference: str) -> float:
    """Ratio of predicted word count to reference word count."""
    pred_count = len(predicted.split())
    ref_count = len(reference.split())
    if ref_count == 0:
        return 0.0
    return pred_count / ref_count
```

## Factory functions

```python
from gmpp.registry import create_component, get_component, get_metric

# Create a component instance by name
comp = create_component("trafilatura", favor_precision=True)

# Get the class (without instantiating)
cls = get_component("trafilatura")

# Get a metric function
fn = get_metric("rouge_lsum")
score = fn("predicted text", "reference text")
```

## Listing what is registered

```python
from gmpp.registry import list_components, list_metrics

# All registered components (name -> class)
print(list_components())

# All registered metrics (name -> callable)
print(list_metrics())
```

From the CLI:

```bash
gmpp list
```

## When is registration optional?

Registration is only needed if you want to use a component in JSON configs
or reconstruct pipelines via `Pipeline.from_config()`. You can always build
pipelines by passing component instances directly:

```python
from gmpp import Pipeline
from gmpp.components.trafilatura import Trafilatura

# This works without any registry involvement
pipe = Pipeline([Trafilatura()])
```

The registry becomes important when you need to serialize and deserialize
pipeline configurations, for example when sharing configs between collaborators
or running pipelines from the CLI.
