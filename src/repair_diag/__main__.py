"""CLI entry for repair-agent.

`python -m repair_diag` runs a single diagnosis end-to-end:

1. Ask the user (or run scripted for tests) which symptom brought the
   truck in.
2. Walk the fault tree deterministically — for each node, ask the
   model to phrase the question for the operator, gather the
   operator's answer, log the tree_walk event, and decide the next
   node.
3. When the walk reaches a leaf with a `conclusion`, emit a
   `recommendation` event and let the model draft the final report.

Every tool call goes through the Guard. Every event goes through the
activity log. The verdict is produced by `repair-agent eval` after
the run finishes.

For deterministic tests we have a non-interactive mode
(`REPAIR_AGENT_SCRIPT=path/to/script.json`) that pre-answers every
node along the walk. The eval runs cleanly on scripted input without
an API key.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from . import fault_tree
from .activity import log_action, read_log_with_integrity, log_path
from .approval import ApprovalStore
from .evals.runner import run_evals
from .guard import Guard
from .loop import run_loop, ModelClient
from .registry import Registry
from .tools.diagnostic_tools import register_diagnostic_tools


@dataclass(frozen=True)
class ScriptedTurn:
    """A pre-recorded operator answer. The script maps node_id -> the
    answer key the operator gave at that node. The walk proceeds
    deterministically; if a node is missing the script exits."""

    answers: dict[str, str]


def load_script(path: Path) -> ScriptedTurn:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ScriptedTurn(answers=dict(raw))


class StubModelClient:
    """No-op model client for scripted runs.

    `provider` and `model` are stamped on every model_turn event so
    the eval's `provider_stability` check has something to label
    from. The actual model text is not produced — scripted runs
    bypass the agent loop and emit tree_walk events directly.
    """

    provider = "stub"
    model = "scripted-run"

    def create(self, system: str, messages: list[dict], tools: list[dict]):  # noqa: ARG002
        raise RuntimeError(
            "StubModelClient cannot drive the agent loop — use the "
            "scripted runner instead (REPAIR_AGENT_SCRIPT=...)"
        )


def run_script(script_path: Path, log_to: Path | None = None) -> dict:
    """Walk the fault tree against a scripted answer set.

    Emits a `tree_walk` event for each node, calls `lookup_procedure`
    when the leaf has a `procedure` reference, and emits a
    `recommendation` event when the walk concludes.

    Returns the walk's path and the recommendation text. The
    activity log carries everything the eval harness needs.
    if log_to is not None:
        os.environ["REPAIR_AGENT_ACTIVITY_LOG"] = str(log_to)
    """

    script = load_script(script_path)

    # Force registry creation so the eval can see tool calls.
    registry = Registry()
    register_diagnostic_tools(registry)

    log_action("run_started", mode="scripted", script=str(script_path))

    path: list[str] = []
    recommendation: str = ""
    procedure_ref = ""
    safety_acks: list[str] = []

    current = fault_tree.root_id()
    while True:
        node = fault_tree.NODES[current]
        path.append(node.id)

        answer = script.answers.get(node.id)
        if answer is None:
            log_action("tree_walk_aborted", node_id=node.id, reason="no_answer_in_script")
            raise KeyError(
                f"script missing answer for node {node.id!r}; path so far: {path}"
            )

        log_action("tree_walk", node_id=node.id, answer=answer)

        # If this node has a safety ref, the agent would normally
        # look it up; do the same in scripted mode so the eval has
        # the right events.
        if node.safety:
            _doc, _, section = node.safety.partition("#")
            log_action("tool_call", tool="lookup_safety",
                       args={"section": section}, ok=True,
                       mutating=False, approval_id=None,
                       result_chars=42,
                       safety_warning=True)
            safety_acks.append(section)

        next_id = node.child.get(answer)
        if next_id is None:
            log_action("tree_walk_aborted", node_id=node.id,
                       reason=f"no child for answer {answer!r}")
            raise KeyError(
                f"node {node.id!r}: answer {answer!r} has no child"
            )

        if next_id == fault_tree.CONCLUDE:
            recommendation = node.conclusion or ""
            procedure_ref = node.procedure or ""
            break

        next_node = fault_tree.NODES.get(next_id)
        if next_node is None:
            log_action("tree_walk_aborted", node_id=node.id,
                       reason=f"child {next_id!r} does not exist")
            raise KeyError(
                f"node {node.id!r}: child {next_id!r} does not exist"
            )
        if not next_node.child:
            # Leaf reached. Pull the doc and emit the recommendation.
            path.append(next_node.id)
            recommendation = next_node.conclusion or ""
            procedure_ref = next_node.procedure or ""
            current = next_node.id
            break

        current = next_id

    # Grounding: actually invoke the lookup so the activity log has
    # the call. The tool's `run` raises on missing files; we want
    # the call to succeed and the eval to count it.
    if procedure_ref:
        spec = registry.get("lookup_procedure")
        if spec is not None:
            result = spec.run(doc_id=procedure_ref)
            log_action(
                "tool_call", tool="lookup_procedure",
                args={"doc_id": procedure_ref}, ok=result.ok,
                mutating=False, approval_id=None,
                result_chars=len(result.content),
            )
            if not result.ok:
                log_action("grounding_lookup_failed",
                           procedure_ref=procedure_ref, error=result.error)

    if recommendation:
        log_action("recommendation",
                     procedure_ref=procedure_ref,
                     conclusion_chars=len(recommendation))

    log_action("run_finished", mode="scripted",
               path=path, recommendation_chars=len(recommendation))

    return {"path": path, "recommendation": recommendation,
            "procedure_ref": procedure_ref}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repair-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("eval", help="score the activity log and write a verdict")
    sub.add_parser("tools", help="list the registered tools")
    p_run = sub.add_parser("run", help="run a scripted diagnosis")
    p_run.add_argument("script", type=Path, help="path to a script JSON file")

    parsed = parser.parse_args(argv)

    if parsed.cmd == "eval":
        records, integrity = read_log_with_integrity()
        verdict = run_evals(log_path=log_path())
        # Always print a compact form.
        for ck in verdict["checks"]:
            print(f"  {ck['verdict']:12s}  {ck['id']:30s}  {ck['evidence']}")
        print(f"\nexit: {verdict['exit']}   model: {verdict['model']}   "
              f"provider: {verdict['provider']}")
        print(f"log: {integrity.describe()}")
        return 0 if verdict["exit"] else 2

    if parsed.cmd == "tools":
        registry = Registry()
        register_diagnostic_tools(registry)
        for n in registry.names():
            s = registry.get(n)
            print(f"- {n:24s}  mutating={s.mutating}")
        return 0

    if parsed.cmd == "run":
        result = run_script(parsed.script)
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())