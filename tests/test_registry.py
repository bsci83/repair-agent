"""Registry tests — the tool surface and the mutating-required contract."""

from __future__ import annotations

import pytest

from repair_diag.registry import Registry, ToolSpec
from repair_diag.types import ToolResult


def _stub_spec(name: str, mutating: bool = False) -> ToolSpec:
    return ToolSpec(
        name=name,
        description="test",
        schema={"type": "object", "properties": {}},
        mutating=mutating,
        run=lambda **kw: ToolResult(True, "ok"),
    )


def test_register_and_get():
    r = Registry()
    r.register(_stub_spec("a"))
    r.register(_stub_spec("b"))
    assert r.get("a") and r.get("b")
    assert r.get("c") is None


def test_double_register_raises():
    r = Registry()
    r.register(_stub_spec("a"))
    with pytest.raises(ValueError, match="already registered"):
        r.register(_stub_spec("a"))


def test_schemas_anthropic_shape():
    r = Registry()
    r.register(_stub_spec("a"))
    schemas = r.schemas()
    assert schemas == [{
        "name": "a", "description": "test",
        "input_schema": {"type": "object", "properties": {}},
    }]


def test_mutating_flag_required_at_construction():
    """Forgetting mutating=True is a TypeError, not a silent False."""
    with pytest.raises(TypeError):
        ToolSpec(  # type: ignore[call-arg]
            name="bad", description="d", schema={},
            run=lambda **kw: None,
        )


def test_render_falls_back_to_args_when_no_renderer():
    r = Registry()
    r.register(_stub_spec("a"))
    spec = r.get("a")
    text = spec.render_for_approval({"z": 1, "a": 2})
    # Canonical: sorted by key.
    assert text == "a: 2\nz: 1"


def test_model_callable_filter():
    """A tool registered with model_callable=False is hidden from the
    schemas() output but still callable via registry.get()."""
    r = Registry()
    hidden = ToolSpec(
        name="hidden", description="t",
        schema={"type": "object", "properties": {}},
        mutating=False, run=lambda **kw: ToolResult(True, "ok"),
        model_callable=False,
    )
    r.register(hidden)
    assert r.get("hidden") is not None
    assert r.schemas() == []  # filtered out
    assert r.names() == ["hidden"]  # still in registry