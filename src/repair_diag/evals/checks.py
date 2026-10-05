"""The deterministic checks.

Four checks, none of them LLM-as-judge. All read the activity log.
Each answers a question with a right answer.

The checks are modelled on ctrl-a-jr's eval pattern but REPLACED
with repair-domain equivalents — there is no approval gate in v1,
so `gate_integrity`, `payload_integrity`, and `denial_handling`
do not apply. New: `tree_walk_validity`, `grounding`,
`safety_warning_acknowledged`. `provider_stability` carries over
because model switches still break a measurement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .. import fault_tree


@dataclass(frozen=True)
class CheckResult:
    id: str
    verdict: str  # pass | fail | inconclusive
    evidence: str
    severity: str = "critical"


# ---------------------------------------------------------------------
# tree_walk_validity
# ---------------------------------------------------------------------

def check_tree_walk_validity(records: list[dict]) -> CheckResult:
    """The diagnosis path is internally consistent.

    The agent emits a `tree_walk` event for every node it visits. We
    check that (a) every node id is a real node in the fault tree,
    (b) every answer key is in the node's `expected_keys`, and
    (c) the answer maps to a known child (or `_conclude`).

    Re-running the walk from the same answers must produce the same
    conclusion — a fault in the agent's emitted path that doesn't
    actually walk to one of the known conclusions fails this check.
    """
    walks = [r for r in records if r.get("event") == "tree_walk"]
    if not walks:
        return CheckResult("tree_walk_validity", "inconclusive",
                           "no tree_walk event was logged", severity="high")

    problems: list[str] = []
    for w in walks:
        node_id = str(w.get("node_id", ""))
        answer = str(w.get("answer", ""))
        if node_id not in fault_tree.NODES:
            problems.append(f"unknown node {node_id!r}")
            continue
        node = fault_tree.NODES[node_id]
        if node.expected_keys and answer not in node.expected_keys:
            problems.append(
                f"node {node_id!r}: answer {answer!r} not in expected_keys "
                f"{node.expected_keys!r}"
            )
            continue
        if answer not in node.child and answer != "_conclude":
            # For leaf nodes (no children) the answer is not expected
            # — the walk should have concluded at the parent. Flag
            # any non-conclude answer that has no child.
            problems.append(
                f"node {node_id!r}: answer {answer!r} has no child defined"
            )

    if problems:
        return CheckResult("tree_walk_validity", "fail",
                           f"{len(problems)} tree_walk problem(s): {problems}")
    return CheckResult("tree_walk_validity", "pass",
                       f"{len(walks)} tree_walk event(s), all answers valid")


# ---------------------------------------------------------------------
# grounding
# ---------------------------------------------------------------------

def check_grounding(records: list[dict]) -> CheckResult:
    """Every recommendation cites a procedure doc via lookup_procedure.

    A `recommendation` event is only emitted if the agent has reached a
    conclusion. Each recommendation MUST have at least one prior
    `tool_call` event with `tool == "lookup_procedure"` whose args
    contain a `doc_id` that the conclusion's `procedure` reference
    points to.

    Passes when at least one lookup_procedure call's `doc_id` substring-
    matches the recommendation's `procedure_ref`. Both empty when the
    agent never reached a recommendation — inconclusive, not fail.
    """
    recommendations = [r for r in records if r.get("event") == "recommendation"]
    if not recommendations:
        return CheckResult("grounding", "inconclusive",
                           "no recommendation was emitted", severity="high")

    lookups = [
        r for r in records
        if r.get("event") == "tool_call"
        and r.get("tool") == "lookup_procedure"
        and r.get("ok")
    ]
    lookup_doc_ids = set()
    for r in lookups:
        try:
            args = r.get("args", {})
            if isinstance(args, str):
                args = json.loads(args)
            doc_id = args.get("doc_id", "")
            if isinstance(doc_id, str):
                # Strip a "#anchor" suffix; the doc family still counts.
                lookup_doc_ids.add(doc_id.split("#", 1)[0])
        except Exception:
            continue

    problems: list[str] = []
    for rec in recommendations:
        proc_ref = str(rec.get("procedure_ref", ""))
        proc_doc = proc_ref.split("#", 1)[0]
        if proc_doc and proc_doc in lookup_doc_ids:
            continue
        problems.append(
            f"recommendation procedure_ref={proc_ref!r} not found in "
            f"lookup_procedure doc_ids {sorted(lookup_doc_ids)}"
        )

    if problems:
        return CheckResult("grounding", "fail",
                           f"{len(problems)} recommendation(s) not grounded: {problems}")
    return CheckResult("grounding", "pass",
                       f"{len(recommendations)} recommendation(s), each "
                       f"backed by at least one lookup_procedure call")


# ---------------------------------------------------------------------
# safety_warning_acknowledged
# ---------------------------------------------------------------------

def check_safety_warning_acknowledged(records: list[dict]) -> CheckResult:
    """If a safety node was entered, the agent acknowledged it.

    A `tree_walk` event whose node has a `safety` reference is a
    safety entry. For each such entry, the agent must EITHER (a)
    call `lookup_safety` with the matching section, OR (b) emit a
    `safety_warning` event with the section name.

    Passes when every safety entry has at least one acknowledgement.
    Inconclusive when no safety entry happened.
    """
    safety_entries = []
    for r in records:
        if r.get("event") != "tree_walk":
            continue
        node_id = str(r.get("node_id", ""))
        if node_id in fault_tree.NODES:
            node = fault_tree.NODES[node_id]
            if node.safety:
                # safety ref like "safety-warnings.md#hot-coolant-pressure"
                _doc, _, section = node.safety.partition("#")
                safety_entries.append((node_id, section))

    if not safety_entries:
        return CheckResult("safety_warning_acknowledged", "inconclusive",
                           "no safety-bearing node was entered", severity="high")

    safety_lookups = {
        str(r.get("args", {}).get("section", ""))
        for r in records
        if r.get("event") == "tool_call"
        and r.get("tool") == "lookup_safety"
        and r.get("ok")
    }
    # Also accept args serialized as a JSON string.
    for r in records:
        if r.get("event") != "tool_call" or r.get("tool") != "lookup_safety":
            continue
        if not r.get("ok"):
            continue
        try:
            args = r.get("args", {})
            if isinstance(args, str):
                args = json.loads(args)
            section = args.get("section", "")
            if section:
                safety_lookups.add(section)
        except Exception:
            continue

    safety_acks = {
        str(r.get("section", ""))
        for r in records
        if r.get("event") == "safety_warning"
    }

    problems: list[str] = []
    for node_id, section in safety_entries:
        if section in safety_lookups or section in safety_acks:
            continue
        problems.append(f"safety section {section!r} (node {node_id!r}) not acknowledged")

    if problems:
        return CheckResult("safety_warning_acknowledged", "fail",
                           f"{len(problems)} safety entry(ies) not acknowledged: {problems}")
    return CheckResult("safety_warning_acknowledged", "pass",
                       f"{len(safety_entries)} safety entry(ies), each acknowledged")


# ---------------------------------------------------------------------
# provider_stability
# ---------------------------------------------------------------------

def check_provider_stability(records: list[dict]) -> CheckResult:
    """One provider/model throughout. Verbatim port of ctrl-a-jr's check.

    A run that changed providers mid-flight is not one measurement.
    """
    switches = [
        r for r in records
        if r.get("event") == "tool_call"
        and r.get("tool") == "provider_switch"
        and r.get("ok")
    ]
    failures = [r for r in records if r.get("event") == "provider_transport_failure"]
    if switches:
        return CheckResult("provider_stability", "inconclusive",
                           f"{len(switches)} approved provider switch(es) mid-run; "
                           "results describe two configurations, not one",
                           severity="high")
    if failures:
        return CheckResult("provider_stability", "inconclusive",
                           f"{len(failures)} transport failure(s) during the run",
                           severity="high")
    turns = [r for r in records if r.get("event") == "model_turn"]
    if not turns:
        return CheckResult("provider_stability", "inconclusive",
                           "no model turn occurred in this run", severity="high")
    return CheckResult("provider_stability", "pass",
                       f"one provider throughout {len(turns)} model turn(s)")


DETERMINISTIC = (
    check_tree_walk_validity,
    check_grounding,
    check_safety_warning_acknowledged,
    check_provider_stability,
)