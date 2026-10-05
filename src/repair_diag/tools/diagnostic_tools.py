"""Read-only tools for the diagnostic agent.

Three tools, all `mutating=False`. They are the only surface the
agent has on the knowledge corpus — the agent cannot read the docs
directly.

`lookup_procedure(doc_id)` is the grounding tool. Every recommendation
the agent makes must be backed by at least one call to this tool —
the eval check `grounding` enforces that.

`lookup_safety(section)` is the safety-warning tool. When the fault
tree's path passes through a node with a `safety` reference, the
agent must either cite the safety section via this tool or surface
the warning explicitly in its prose.

`list_fault_families()` is a navigational tool — it returns the
family roots so the agent can orient at the start of a diagnosis.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..registry import Registry, ToolSpec
from ..types import ToolResult

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
KNOWLEDGE_DIR = _KNOWLEDGE_DIR


def _read_doc(doc_id: str) -> str:
    """Return the body of a knowledge doc. Strips the front-matter
    disclaimer and the citation footer, returning only the substantive
    content the agent should cite from."""
    # doc_id may include an anchor like "series60-cooling.md#water-pump"
    name, _, _anchor = doc_id.partition("#")
    # Resolve relative to the knowledge dir; refuse path-escape.
    if ".." in name or name.startswith("/") or "\\" in name:
        raise ValueError(f"refusing to resolve doc id {doc_id!r}")
    path = KNOWLEDGE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"no knowledge doc named {name!r}")
    return path.read_text(encoding="utf-8")


def _wrap(fn):
    """Return a ToolResult-wrapping adapter. Failure is a value,
    never an exception."""
    def inner(**kwargs):
        try:
            return ToolResult(True, fn(**kwargs))
        except Exception as exc:  # noqa: BLE001
            return ToolResult(False, "", str(exc))
    return inner


def _list_doc_ids() -> list[str]:
    return sorted(p.name for p in KNOWLEDGE_DIR.glob("*.md"))


def register_diagnostic_tools(registry: Registry) -> None:
    registry.register(ToolSpec(
        name="lookup_procedure",
        description=(
                "Look up a procedure document from the knowledge corpus by "
                "doc id (e.g. 'series60-injector.md'). Returns the document "
                "body. Use this BEFORE making a recommendation — every "
                "conclusion you reach must be backed by at least one call to "
                "this tool. The doc id you pass is logged in the activity "
                "log and verified by the eval harness against the "
                "recommendation."
        ),
        schema={
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "The knowledge doc id (filename without the dir).",
                },
            },
            "required": ["doc_id"],
        },
        mutating=False,
        run=_wrap(lambda doc_id: _read_doc(doc_id)),
    ))

    registry.register(ToolSpec(
        name="lookup_safety",
        description=(
                "Look up a safety warning section (e.g. 'hot-coolant-pressure') "
                "from the safety-warnings doc. Use this when the diagnosis "
                "path enters a node marked with a safety reference — the "
                "agent must surface the warning to the operator before "
                "recommending action."
        ),
        schema={
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "The section anchor (e.g. 'hot-coolant-pressure').",
                },
            },
            "required": ["section"],
        },
        mutating=False,
        run=_wrap(lambda section: _extract_safety_section(section)),
    ))

    registry.register(ToolSpec(
        name="list_fault_families",
        description=(
                "List the fault families the diagnosis routes through. "
                "Returns the family names and one-line summaries. Use this "
                "at the start of a diagnosis to orient."
        ),
        schema={"type": "object", "properties": {}},
        mutating=False,
        run=_wrap(lambda: json.dumps(_fault_families(), indent=2)),
    ))


def _extract_safety_section(section: str) -> str:
    """Extract a single safety section from safety-warnings.md by heading.

    Section names are slug-style ("hot-coolant-pressure") and matched
    case-insensitively against any `## Heading` whose slug matches.
    """
    text = _read_doc("safety-warnings.md")
    target_slug = _slugify(section)
    lines = text.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.startswith("## "):
            if capturing:
                break
            heading = line[3:].strip()
            if _slugify(heading) == target_slug:
                capturing = True
                out.append(line)
                continue
        if capturing:
            out.append(line)
    if not out:
        raise ValueError(f"no safety section matching {section!r}")
    return "\n".join(out).strip()


def _slugify(text: str) -> str:
    """Lowercase, replace spaces with dashes, drop punctuation."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _fault_families() -> dict:
    """Static descriptions of the five families the diagnosis routes through."""
    return {
        "families": [
            {"key": "no_start", "summary": "Engine doesn't fire — fuel or starter."},
            {"key": "injector", "summary": "Rough idle, black smoke, or low power."},
            {"key": "cooling", "summary": "Overheating or white smoke."},
            {"key": "electrical", "summary": "Sudden shutdown or stumble-then-stop."},
            {"key": "egr", "summary": "EGR code or visible soot."},
        ],
        "knowledge_docs": _list_doc_ids(),
    }