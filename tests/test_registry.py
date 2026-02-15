"""Tests for gmpp.registry."""

from __future__ import annotations

import pytest

from gmpp import (
    Component,
    Document,
    create_component,
    list_components,
    list_metrics,
    register_component,
    register_metric,
)
from gmpp.registry import get_component, get_metric


class TestRegisterComponent:
    def test_register_and_create(self) -> None:
        # "uppercase" is registered in conftest.py
        comp = create_component("uppercase")
        assert isinstance(comp, Component)

    def test_list_components(self) -> None:
        components = list_components()
        assert "uppercase" in components
        assert isinstance(components, dict)

    def test_get_component(self) -> None:
        cls = get_component("uppercase")
        assert issubclass(cls, Component)

    def test_unknown_component_raises(self) -> None:
        with pytest.raises(KeyError, match="No component registered"):
            get_component("nonexistent_component_xyz")

    def test_create_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="No component registered"):
            create_component("nonexistent_component_xyz")


class TestRegisterMetric:
    def test_register_and_retrieve(self) -> None:
        @register_metric("dummy_metric")
        def dummy(predicted: str, reference: str) -> float:
            return 1.0

        metrics = list_metrics()
        assert "dummy_metric" in metrics

        fn = get_metric("dummy_metric")
        assert fn("a", "b") == 1.0

    def test_unknown_metric_raises(self) -> None:
        with pytest.raises(KeyError, match="No metric registered"):
            get_metric("nonexistent_metric_xyz")
