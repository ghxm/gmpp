"""Component and metric registries for config-driven pipeline reconstruction."""

import warnings
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from gmpp.component import Component

# Module-level registries
_components: dict[str, type] = {}
_metrics: dict[str, Callable[..., float]] = {}


# -- decorators ---------------------------------------------------------------


def register_component(name: str) -> Callable[[type], type]:
    """Class decorator that registers a Component subclass under *name*."""

    def wrapper(cls: type) -> type:
        if name in _components:
            warnings.warn(
                f"Overwriting component {name!r} "
                f"(was {_components[name].__name__}, now {cls.__name__}).",
                stacklevel=2,
            )
        _components[name] = cls
        cls._registered_name = name
        return cls

    return wrapper


def register_metric(name: str) -> Callable[[Callable], Callable]:
    """Function decorator that registers a metric callable under *name*."""

    def wrapper(fn: Callable[..., float]) -> Callable[..., float]:
        _metrics[name] = fn
        return fn

    return wrapper


# -- lookup / factory --------------------------------------------------------


def get_component(name: str) -> type:
    """Return the Component class registered under *name*.

    Raises:
        KeyError: If no component is registered under *name*.
    """
    try:
        return _components[name]
    except KeyError:
        raise KeyError(
            f"No component registered under {name!r}. "
            f"Available: {list(_components)}"
        ) from None


def get_metric(name: str) -> Callable[..., float]:
    """Return the metric callable registered under *name*.

    Raises:
        KeyError: If no metric is registered under *name*.
    """
    try:
        return _metrics[name]
    except KeyError:
        raise KeyError(
            f"No metric registered under {name!r}. "
            f"Available: {list(_metrics)}"
        ) from None


def create_component(name: str, **params: Any) -> "Component":
    """Instantiate the Component registered under *name* with *params*."""
    cls = get_component(name)
    return cls(**params)


def list_components() -> dict[str, type]:
    """Return a copy of the component registry."""
    return dict(_components)


def list_metrics() -> dict[str, Callable[..., float]]:
    """Return a copy of the metric registry."""
    return dict(_metrics)
