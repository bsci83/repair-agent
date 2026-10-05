# repair-agent

A hand-rolled diagnostic agent for the **Detroit Diesel Series 60**
that walks a mechanic through fault diagnosis by asking one question
at a time and citing every recommendation against a procedure
document. The architecture is a direct port of
[`ctrl-a-jr`](https://github.com/bsci83/ctrl-a-jr)'s agent loop
to a deterministic fault-tree.

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** The fault tree and the procedure documents in
> `src/repair_diag/knowledge/` are authored from public DDC technical
> service bulletins and SAE papers. Always follow the OEM
> documentation for actual service work.

---

## The one idea worth taking away

**The model classifies. The code decides.**

The agent asks the operator a question; the operator answers; the
model writes the prose. **Which question to ask next** is not the
model's — it's a deterministic decision-tree walk over
`src/repair_diag/fault_tree.py`. The tree is data, the walk is pure.
A misclassification produces a wrong path through the tree, not a
fabricated fix.

This is the same commitment ctrl-a-jr made for pricing (`the model
classifies the request, the code computes the cost`). Porting it
verbatim was a deliberate choice: a fault tree that the model could
re-route at will isn't a tree, it's a graph, and a graph is harder
to evaluate.

---

## 1. Run it

The `run` subcommand takes a script of pre-recorded operator answers
and walks the tree deterministically. The `eval` subcommand reads
the resulting activity log and emits a verdict.

```bash
PYTHONPATH=src python -m repair_diag run examples/diagnose-egr-cooler.json
PYTHONPATH=src python -m repair_diag eval
```

Sample run output:

```
{
  "path": [
    "root",
    "fam_egr",
    "egr_code",
    "conclude_egr_cooler_plugged"
  ],
  "procedure_ref": "series60-egr.md#cooler",
  "recommendation": "EGR code after the truck sat — EGR cooler plugged with soot. Remove, clean, and pressure-test; replace if the cooler is perforated or the cores are packed."
}
```

The `eval` subcommand:

```
pass          tree_walk_validity              12 tree_walk event(s), all answers valid
pass          grounding                       4 recommendation(s), each backed by at least one lookup_procedure call
pass          safety_warning_acknowledged     2 safety entry(ies), each acknowledged
inconclusive  provider_stability              no model turn occurred in this run

exit: True   model: unknown   provider: unknown
log: 30 record(s), no losses
```

## 2. Tests

```bash
python -m pytest tests/                  # 45 tests, ~0.3s
```

The tests exercise every load-bearing invariant in the architecture:
the loop's four invariants, the activity log's attribution rule,
the registry's `mutating`-required contract, the fault tree's
reachability and leaf discipline, and each of the four eval checks
for pass / fail / inconclusive outcomes.

## 3. Architecture

```
scripted answers (run) ──► walk loop ──► Guard ──► lookup_procedure / lookup_safety / list_fault_families
                                  │                  │
                                  │                  └─► knowledge/ (8 procedure docs)
                                  │
                                  └─► append-only activity log ──► eval runner ──► verdict.json
```

| Module | Lines | What it does |
|---|---|---|
| `types.py` | 36 | `ToolResult`, `Decision`, `ApprovalRecord` |
| `registry.py` | 60 | `ToolSpec` with required `mutating: bool` |
| `activity.py` | 175 | Append-only JSONL; attribution applied last |
| `approval.py` | 97 | Payload-hash pattern, unused in v1 |
| `guard.py` | 78 | The chokepoint; every tool call passes through |
| `loop.py` | 224 | Hand-rolled agent loop, 4 invariants, MAX_ROUNDS=8 |
| `fault_tree.py` | 567 | 42-node decision tree, pure walk function |
| `tools/diagnostic_tools.py` | 168 | 3 read-only tools, all `mutating=False` |
| `evals/checks.py` | 244 | 4 deterministic checks, no LLM-as-judge |
| `evals/runner.py` | 122 | Score the log, emit `verdict.json` |

Everything in the loop table is a direct port of ctrl-a-jr. The two
new pieces are `fault_tree.py` (the deterministic decision tree) and
`tools/diagnostic_tools.py` (the surface on the knowledge corpus).
The four evals are rewritten: ctrl-a-jr's gate checks don't apply
because v1 has no mutating tool.

## 4. Reliability testing methodology

This is the part most agent demos cannot show, so it is the part
this project invested in — modelled on the same shape as ctrl-a-jr.

### The evidence is a byproduct of the architecture, not a separate effort

Every tool call passes through `Guard.dispatch`. The activity log
is the only input the eval reads.

### The four checks

| # | Check | Passes when |
|---|---|---|
| 1 | **`tree_walk_validity`** | Every `tree_walk` event's node id is a real node in `fault_tree.py`, every answer key is in the node's `expected_keys`, and every answer maps to a known child. |
| 2 | **`grounding`** | Every `recommendation` event's `procedure_ref` was the target of at least one prior `lookup_procedure` tool call. |
| 3 | **`safety_warning_acknowledged`** | If the walk passed through any node with `safety != None`, the agent either called `lookup_safety` for that section or emitted a `safety_warning` event. |
| 4 | **`provider_stability`** | One provider/model throughout. Verbatim port of ctrl-a-jr's check. |

All four are deterministic. No model is involved in judging.

### What makes the numbers trustworthy is what they refuse to claim

- **`provider_stability` is inconclusive when no model turn occurred.** A scripted run that bypasses the model loop has nothing to label; the check refuses to pass on absence.
- **A damaged log cannot produce a green verdict.** Malformed lines and write failures are counted by `read_log_with_integrity` and reported in the verdict.
- **The verdict labels itself from the log.** A caller cannot mislabel which model produced the run.

### Current verdict (4 scripted diagnoses across 3 fault families + EGR)

```
exit: true   model: unknown   provider: unknown
  pass          tree_walk_validity           held across 12 tree_walk event(s)
  pass          grounding                    held across 4 recommendation(s)
  pass          safety_warning_acknowledged  held across 2 safety entry(ies)
  inconclusive  provider_stability           no model turn occurred in this run
  log integrity  30 record(s), no losses
```

The single inconclusive is the honest answer for a scripted run —
`provider_stability` lights up when an actual agent loop runs, not
when a script drives the tree directly.

## 5. Limitations, stated plainly

- **No mutating tool.** v1 has no side-effecting tool, so the guard's
  approval branch never runs. The pattern is preserved for when one
  lands; the loop does not depend on a mutating tool existing.
- **No resumable driver.** ctrl-a-jr's `advance` path is not
  ported. The seam for it is preserved at the `run_round` /
  `execute_uses` boundary.
- **Provider stability is a check, not a guarantee.** The check
  reports when the model changes mid-run; it does not prevent it.
- **Cross-tool equivalence is not detected.** A denied
  `lookup_procedure` followed by the same information requested via
  `lookup_safety` would not be caught (the eval is on the answer, not
  on the question).
- **The recommendation prose is model-authored.** The conclusion
  text and the path through the tree are deterministic, but the
  prose the model uses to phrase the recommendation is not. A
  future version can require structured output for the final
  recommendation.
- **The fault tree is a teaching artifact, not production data.**
  It is intentionally small (42 nodes) and authored from public
  sources. A real shop's diagnostic decision-making would draw on
  the full DDC service library and accumulated tribal knowledge.

## License

MIT. See `LICENSE`.

## Source

Ported from [`ctrl-a-jr`](https://github.com/bsci83/ctrl-a-jr), a
public agent I built earlier in 2026 for the Multi-App AI Agent
Hackathon. Same author, same loop, same eval pattern — different
domain.