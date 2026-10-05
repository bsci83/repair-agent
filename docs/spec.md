# Repair-Diagnosis Agent — Spec

**Repo:** `repair-agent/`  (working dir: `C:\Users\bifil\dev\repair-agent`)
**Started:** 2026-10-04
**Status:** Pre-build. This document is the contract. Code follows.

---

## 1. What this is

A CLI tool that walks a mechanic through diagnosing a fault on a Detroit
Diesel Series 60 engine. The user types a starting symptom; the agent
asks one question at a time, classifies the answer, decides which
question to ask next, and concludes with a suspected fault and a
procedure to follow. Every recommendation is grounded in a procedure
document the agent retrieved, with the citation in the transcript.

The architecture is a **direct port of `ctrl-a-jr`'s hand-rolled agent
loop, registry, guard, activity log, and eval runner.** The new piece
is a **deterministic fault-tree** that decides which question to ask
next based on the answers so far. The model asks the question; the
code decides what to ask next. ("The model classifies. The code
decides.")

This repo is intentionally read-only against the user's machine.
There is no mutating tool with side effects, no approval gate, no
deployment. v1 is a CLI transcript + a deterministic verdict.

---

## 2. Porting decisions (from `ctrl-a-jr`)

**Verbatim ports** — the architecture is the same:
- `src/repair_diag/types.py` — `ToolResult`, `Decision`, `ApprovalRecord`.
- `src/repair_diag/registry.py` — `ToolSpec` with required `mutating: bool`.
- `src/repair_diag/activity.py` — append-only JSONL, attribution-last.
- `src/repair_diag/approval.py` — payload integrity pattern (kept unused).

**Near-verbatim ports** — same shape, fewer tools:
- `src/repair_diag/loop.py` — `run_round`, `run_loop`, `MAX_ROUNDS = 8`.
  No resumable driver in v1 (`resume.py` / `advance`).
- `src/repair_diag/guard.py` — same chokepoint, but every tool is
  `mutating=False`, so the gate is a thin pass-through. The pattern
  is here for when we add a real mutating tool later.

**Replaced** — the eval harness changes:
- `src/repair_diag/evals/checks.py` — drop `gate_integrity`,
  `payload_integrity`, `denial_handling` (no gate in v1).
  Add: `tree_walk_validity`, `grounding`, `safety_warning_acknowledged`,
  `provider_stability` (kept from ctrl-a-jr — still load-bearing).
- `src/repair_diag/evals/runner.py` — same shape, fewer checks.

**Skipped** — not ported in v1:
- `resume.py`, `approver_remote.py`, `server.py` — no resumable driver.
- `pricing.py` equivalent — replaced by `fault_tree.py`.
- `fixtures.py`, `cli.py` machinery, `doctor.py`, `vercel.json`,
  `verdict.json` schema versioning — none of the deployment plumbing.

---

## 3. Fault-tree shape (the new piece)

The fault tree is **a frozen dict of nodes, keyed by id**, and a
**pure walk function.** No I/O, no model calls, no globals. The model
classifies the answer (yes / no / which / n_a); the code decides
which node comes next.

```python
@dataclass(frozen=True)
class Node:
    id: str
    question: str                 # the question text the model sees
    expected_keys: tuple[str, ...] # the valid answer keys ("yes", "no", ...)
    child: Mapping[str, str]      # answer_key -> next_node_id (or "_conclude")
    procedure: str | None = None   # citation ref if this is a leaf
    conclusion: str | None = None  # the leaf label when we conclude here
    safety: str | None = None       # safety-warning doc id if entered
```

**Walk contract:**
```python
walk(start: str, answers: Mapping[str, str]) -> tuple[list[str], str]
```
Returns `(path_of_node_ids, leaf_conclusion)`. Deterministic, pure,
testable without a model. A wrong answer key raises `KeyError` — the
eval harness counts that as a `tree_walk_validity` failure.

**Tree size target:** ~25-35 nodes across 4 fault families
(injector, EGR, cooling, electrical). One root node ("What's the
symptom?") branches to family roots, which branch to leaf
conclusions.

---

## 4. Knowledge corpus (the `docs/`)

**Path A** — authored teaching corpus, not a substitute for the OEM
service manual. Every document carries a header stating that.

Eight documents (~30-60 paragraphs total):

| Doc | Purpose |
|---|---|
| `series60-symptoms.md` | The symptom catalog the agent reads first |
| `series60-fault-tree.md` | The fault-tree topology (mirror of `fault_tree.py`) |
| `series60-injector.md` | Injector / fueling family procedures |
| `series60-egr.md` | EGR / emissions family procedures |
| `series60-cooling.md` | Cooling-system family procedures |
| `series60-electrical.md` | Wiring / sensor / DDEC family procedures |
| `series60-sensors.md` | Sensor-by-sensor troubleshooting |
| `safety-warnings.md` | Hot coolant, pressurized oil, ECM damage hazards |

Each doc has a `## Citations` footer listing the public sources it
was authored from (SAE papers, DDC service bulletins in the public
domain, owner-forum syntheses). No OEM-proprietary text.

---

## 5. Eval pattern (deterministic only)

Four checks, none of them LLM-as-judge. All read the activity log.

| Check | Passes when |
|---|---|
| `tree_walk_validity` | Every node reached by the diagnosis path matches a real node in `fault_tree.py`, and the answer keys are all members of the node's `expected_keys`. |
| `grounding` | Every recommendation (conclusion text) cites at least one `lookup_procedure` tool call with a doc id present in `docs/`. |
| `safety_warning_acknowledged` | If the diagnosis path passed through any node with `safety != None`, the agent either (a) cited the safety doc via `lookup_procedure`, or (b) emitted a text block with the safety-warning keyword list. |
| `provider_stability` | One provider/model throughout. Same check as ctrl-a-jr, kept because model switches still break a measurement. |

**Verdict shape (smaller than ctrl-a-jr):**
```json
{
  "schema": "repair-agent/verdict.v1",
  "checks": [...],
  "log_integrity": {...},
  "exit": <bool>,
  "model": "<labelled from log>",
  "provider": "<labelled from log>"
}
```

---

## 6. Scope contract (the "no when does this balloon" rules)

**DONE** = `python -m repair_diag` runs a single diagnosis end-to-end
against an interactive user, writes an activity log, the eval runner
scores it, and a green verdict is committed alongside the code.

**NOT doing:**
- Web UI, API, deployment
- Resumability, multi-process state
- Approval gate (no mutating tool in v1)
- LLM-as-judge evals (deterministic-only is the point)
- Cribbing the actual OEM service manual (copyright + scope)
- Multi-language support
- v2.0 of any framework this builds on

---

## 7. Commit trail (the build artifacts)

Every code change is one commit. Commit cadence follows `ctrl-a-jr`:
- `chore:` for scaffolding (LICENSE, pyproject, .gitignore, README)
- `feat(scope):` for new modules
- `fix:` for runtime bugs caught during the build
- `docs:` for knowledge/ additions
- `test:` for tests
- Final commit: `chore: pass eval v1, record verdict.json` with the
  verdict file committed as the build artifact.

Target: 20-30 commits over one focused session.

---

## 8. What's NOT in this batch (deferred)

- Repair-corpus expansion beyond the 8 teaching docs
- Resumable driver / multi-process state
- Any mutating tool that would re-enable the approval gate
- LLM-as-judge evals
- Public push (the local repo + commit trail is the artifact;
  the public push is a separate decision once the verdict is green)