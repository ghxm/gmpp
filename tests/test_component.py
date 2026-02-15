"""Tests for gmpp.component."""

from __future__ import annotations

import pytest

from gmpp import Component, Document, create_component


class TestComponentABC:
    def test_subclass_must_implement_process(self) -> None:
        """A subclass without process() cannot be instantiated."""

        class Incomplete(Component):
            output_field = "text"

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]


class TestComponentParams:
    def test_get_params(self) -> None:
        from tests.conftest import UpperCaseComponent

        comp = UpperCaseComponent()
        params = comp.get_params()
        assert isinstance(params, dict)

    def test_set_params(self) -> None:
        """set_params should set attributes on the instance."""

        class Configurable(Component):
            output_field = "text"

            def __init__(self, alpha: float = 0.5) -> None:
                self.alpha = alpha

            def process(self, doc: Document) -> Document:
                return doc

        comp = Configurable(alpha=0.1)
        assert comp.get_params() == {"alpha": 0.1}

        comp.set_params(alpha=0.9)
        assert comp.alpha == 0.9
        assert comp.get_params() == {"alpha": 0.9}


class TestComponentSerialization:
    def test_to_dict_from_dict(self) -> None:
        # UpperCaseComponent is registered as "uppercase" in conftest
        from tests.conftest import UpperCaseComponent

        comp = UpperCaseComponent()
        config = comp.to_dict()
        assert config["name"] == "uppercase"

        reconstructed = Component.from_dict(config)
        assert isinstance(reconstructed, UpperCaseComponent)


class TestComponentRepr:
    def test_repr_no_params(self) -> None:
        from tests.conftest import UpperCaseComponent

        comp = UpperCaseComponent()
        assert "UpperCaseComponent(" in repr(comp)

    def test_repr_with_params(self) -> None:
        class WithParam(Component):
            output_field = "text"

            def __init__(self, k: int = 3) -> None:
                self.k = k

            def process(self, doc: Document) -> Document:
                return doc

        comp = WithParam(k=5)
        assert repr(comp) == "WithParam(k=5)"
