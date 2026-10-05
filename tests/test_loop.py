"""Loop invariants — the 4 rules that prevent the loop from misbehaving.

The loop uses a real Anthropic client in production; tests instead
use a stub that emits canned tool_use blocks. We exercise invariants
1-4 here.
"""

from __future__ import annotations

from typing import Any

from repair_diag.activity import read_log
from repair_diag.approval import ApprovalStore
from repair_diag.guard import Guard
from repair_diag.loop import (
    MAX_ROUNDS,
    ToolUse,
    _assistant_turn,
    _text_of,
    dispatch_gate,
    execute_uses,
    result_block,
    run_loop,
    run_round,
)
from repair_diag.registry import Registry, ToolSpec
from repair_diag.types import ToolResult, Decision


def _stub_spec(name="echo", mutating=False, result=ToolResult(True, "ok")):
    return ToolSpec(
        name=name, description="t", schema={}, mutating=mutating,
        run=lambda **kw: result,
    )


class _StubModelClient:
    """One canned response per call. `responses[i]` is returned on call i."""
    provider = "stub"
    model = "stub-test"

    def __init__(self, responses):
        self._responses = list(responses)
        self._i = 0

    def create(self, system, messages, tools):  # noqa: ARG002
        r = self._responses[self._i]
        self._i += 1
        return r


def _text_response(text: str) -> Any:
    class _Block:
        type = "text"
        def __init__(self, t): self.text = t
    class _R:
        content = [_Block(text)]
    return _R()


def _tool_use_response(blocks):
    """blocks is list of {id, name, input}."""
    class _Block:
        def __init__(self, **kw):
            self.type = "tool_use"
            self.id = kw["id"]
            self.name = kw["name"]
            self.input = kw["input"]
    class _R:
        content = [_Block(**b) for b in blocks]
    return _R()


def test_text_only_terminates_in_one_round():
    """No tool_use -> done=True on the first round."""
    client = _StubModelClient([_text_response("hello")])
    registry = Registry()
    registry.register(_stub_spec())
    guard = Guard(registry, ApprovalStore(), lambda rec: Decision.APPROVED)
    result = run_loop(client, guard, "sys", "user")
    assert result.text == "hello"
    assert result.rounds == 1
    assert not result.hit_limit


def test_max_rounds_triggers_final_turn():
    """Every turn emits a tool_use, MAX_ROUNDS=8, so we hit the limit
    and the final_turn runs."""
    client = _StubModelClient(
        [_tool_use_response([{"id": f"u{i}", "name": "echo", "input": {}}])
         for i in range(MAX_ROUNDS + 1)]
    )
    registry = Registry()
    registry.register(_stub_spec())
    guard = Guard(registry, ApprovalStore(), lambda rec: Decision.APPROVED)
    result = run_loop(client, guard, "sys", "user")
    assert result.hit_limit
    assert result.rounds == MAX_ROUNDS + 1


def test_execute_uses_emits_one_tool_result_per_use_in_order():
    """Invariant 2: results are in emission order, one per use."""
    uses = [
        ToolUse("a", "echo", {"i": 0}),
        ToolUse("b", "echo", {"i": 1}),
        ToolUse("c", "echo", {"i": 2}),
    ]
    gate = lambda u: ToolResult(True, f"out_{u.input['i']}")
    results, pending = execute_uses(uses, gate)
    assert pending == []
    assert [r["content"] for r in results] == ["out_0", "out_1", "out_2"]


def test_assistant_turn_drops_unknown_blocks():
    """A block type we don't model is DROPPED, not silently included."""
    class _ToolBlock:
        type = "tool_use"
        id = "u1"
        name = "echo"
        input = {}
    class _ThinkingBlock:
        type = "thinking"
        text = "hmm"
    class _R:
        content = [_ToolBlock, _ThinkingBlock]
    turn = _assistant_turn(_R())
    types = [b["type"] for b in turn["content"]]
    assert "thinking" not in types
    assert "tool_use" in types


def test_tool_failure_does_not_abort_loop():
    """Invariant 3: a failing tool becomes an error tool_result."""
    failing_spec = ToolSpec(
        name="boom", description="t", schema={}, mutating=False,
        run=lambda **kw: (_ for _ in ()).throw(RuntimeError("kaboom")),
    )
    client = _StubModelClient([
        _tool_use_response([{"id": "u1", "name": "boom", "input": {}}]),
        _text_response("recovered"),
    ])
    registry = Registry()
    registry.register(failing_spec)
    guard = Guard(registry, ApprovalStore(), lambda rec: Decision.APPROVED)
    result = run_loop(client, guard, "sys", "user")
    assert result.text == "recovered"
    assert not result.hit_limit


def test_run_round_with_no_tools_returns_text_immediately():
    """If the model emits nothing but text, done=True with the text."""
    client = _StubModelClient([_text_response("done")])
    step = run_round(client, "sys", [{"role": "user", "content": "q"}],
                     tools=[], round_index=0, gate=lambda u: ToolResult(False, ""))
    assert step.done
    assert step.text == "done"
    assert step.assistant_turn is None


def test_result_block_shapes_tool_result_for_model():
    use = ToolUse("u1", "echo", {})
    outcome = ToolResult(True, "ok")
    block = result_block(use, outcome)
    assert block["type"] == "tool_result"
    assert block["tool_use_id"] == "u1"
    assert block["is_error"] is False
    assert block["content"] == "ok"


def test_dispatch_gate_never_returns_none():
    """The blocking gate must always answer every tool_use."""
    registry = Registry()
    registry.register(_stub_spec())
    guard = Guard(registry, ApprovalStore(), lambda rec: Decision.APPROVED)
    gate = dispatch_gate(guard)
    out = gate(ToolUse("u1", "echo", {}))
    assert out is not None
    assert out.ok is True