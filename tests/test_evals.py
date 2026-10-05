"""Eval check tests — the four deterministic claims, exercised end-to-end.

Each check has three outcomes: pass, fail, inconclusive. We construct
the synthetic log records that produce each outcome and assert.
"""

from __future__ import annotations

import json

from repair_diag.evals import checks
from repair_diag.evals.checks import (
    check_grounding,
    check_provider_stability,
    check_safety_warning_acknowledged,
    check_tree_walk_validity,
)


def _ok_call(tool, **args):
    return {"event": "tool_call", "tool": tool, "args": args, "ok": True}


def test_tree_walk_validity_pass():
    records = [
        {"event": "tree_walk", "node_id": "root", "answer": "rough_idle"},
        {"event": "tree_walk", "node_id": "fam_injector", "answer": "idle_and_load"},
        {"event": "tree_walk", "node_id": "inj_idle_load", "answer": "black"},
    ]
    r = check_tree_walk_validity(records)
    assert r.verdict == "pass"


def test_tree_walk_validity_fail_on_bad_answer():
    records = [{"event": "tree_walk", "node_id": "root", "answer": "no_such"}]
    r = check_tree_walk_validity(records)
    assert r.verdict == "fail"


def test_tree_walk_validity_inconclusive_when_no_walks():
    r = check_tree_walk_validity([])
    assert r.verdict == "inconclusive"


def test_grounding_pass():
    records = [
        _ok_call("lookup_procedure", doc_id="series60-injector.md"),
        _ok_call("lookup_procedure", doc_id="series60-injector.md#overfueling"),
        {"event": "recommendation",
         "procedure_ref": "series60-injector.md#overfueling"},
    ]
    r = check_grounding(records)
    assert r.verdict == "pass"


def test_grounding_fail_when_no_lookup():
    records = [
        {"event": "recommendation",
         "procedure_ref": "series60-injector.md#overfueling"},
    ]
    r = check_grounding(records)
    assert r.verdict == "fail"


def test_grounding_inconclusive_without_recommendation():
    r = check_grounding([])
    assert r.verdict == "inconclusive"


def test_grounding_accepts_args_as_json_string():
    """The runner serialises args; the check must accept either shape."""
    records = [
        {"event": "tool_call", "tool": "lookup_procedure",
         "args": json.dumps({"doc_id": "series60-injector.md"}), "ok": True},
        {"event": "recommendation",
         "procedure_ref": "series60-injector.md#overfueling"},
    ]
    r = check_grounding(records)
    assert r.verdict == "pass"


def test_safety_warning_pass():
    records = [
        {"event": "tree_walk", "node_id": "ns_fuel", "answer": "yes"},
        {"event": "tool_call", "tool": "lookup_safety",
         "args": {"section": "hot-fuel-pressure"}, "ok": True},
    ]
    r = check_safety_warning_acknowledged(records)
    assert r.verdict == "pass"


def test_safety_warning_fail():
    records = [
        {"event": "tree_walk", "node_id": "ns_fuel", "answer": "yes"},
        # No lookup_safety, no safety_warning event.
    ]
    r = check_safety_warning_acknowledged(records)
    assert r.verdict == "fail"


def test_safety_warning_inconclusive_when_no_safety_node():
    records = [
        {"event": "tree_walk", "node_id": "root", "answer": "rough_idle"},
    ]
    r = check_safety_warning_acknowledged(records)
    assert r.verdict == "inconclusive"


def test_safety_warning_pass_via_safety_warning_event():
    """An explicit `safety_warning` event also counts as acknowledgement."""
    records = [
        {"event": "tree_walk", "node_id": "ns_fuel", "answer": "yes"},
        {"event": "safety_warning", "section": "hot-fuel-pressure"},
    ]
    r = check_safety_warning_acknowledged(records)
    assert r.verdict == "pass"


def test_provider_stability_pass():
    records = [
        {"event": "model_turn", "provider": "anthropic",
         "model": "claude-sonnet-4-5", "round": 1},
        {"event": "model_turn", "provider": "anthropic",
         "model": "claude-sonnet-4-5", "round": 2},
    ]
    r = check_provider_stability(records)
    assert r.verdict == "pass"


def test_provider_stability_inconclusive_on_switch():
    records = [
        {"event": "model_turn", "provider": "anthropic",
         "model": "claude-sonnet-4-5", "round": 1},
        {"event": "tool_call", "tool": "provider_switch", "ok": True},
        {"event": "model_turn", "provider": "openai",
         "model": "gpt-4", "round": 2},
    ]
    r = check_provider_stability(records)
    assert r.verdict == "inconclusive"


def test_provider_stability_inconclusive_without_turns():
    r = check_provider_stability([])
    assert r.verdict == "inconclusive"


def test_deterministic_list_is_complete():
    """Adding a new check without listing it in DETERMINISTIC would
    silently skip it."""
    expected = {
        "tree_walk_validity", "grounding",
        "safety_warning_acknowledged", "provider_stability",
    }
    assert {fn(records=[]).id for fn in checks.DETERMINISTIC} == expected