# Fault tree overview

> **This is a teaching corpus, not a substitute for the OEM service
> manual.** The fault tree in `fault_tree.py` is the deterministic
> decision tree the diagnosis walks. This document is the same tree
> in narrative form.

## shape

```
                       root
                        |
       +--------+-------+-------+-------+-------+-------+
       |        |       |       |       |       |       |
   no_start  rough  over-  black  white  low_  shutting
              idle   heating  smoke  smoke  power    down
       |        |       |       |       |       |       |
   fam_no_   fam_inj fam_cool fam_inj fam_   fam_   fam_
   start              (via    (via   cool    inj    elec
       |        |     white)  black) (via    (via
   ns_fuel  inj_    ...       ...   white)   idle)
       |    idle_load                  ...
       |     ...
```

The tree has 42 nodes total — 1 root, 5 family routing nodes
(`fam_no_start`, `fam_injector`, `fam_cooling`, `fam_electrical`,
`fam_egr`), and the rest as branch-pointers and conclusions. 24 leaves
have a `conclusion` text and a `procedure` reference.

## who classifies what

The agent has the model when it wants to interpret a free-text customer
answer ("Yeah, it kinda stumbles when it's cold, but it's fine when
it's warm"). The agent does NOT have the model when it picks the
next question — that decision is the fault tree's.

A confusion costs nothing if it's caught. The eval check
`tree_walk_validity` records every KeyError the walk raises — a
KeyError means an answer key wasn't in `expected_keys`, or a node id
didn't resolve. Either is a fault in the diagnosis tree, not the
diagnosis, and gets logged.

## why a tree and not a graph

Trees are deterministic. There is one path from the root to every
leaf. Cycles are not expressible. A diagnosis walked along this tree
is a sequence of explicit choices, and the eval harness can verify
each choice against `expected_keys` without an LLM.

A graph would let two symptoms share a leaf — for example, "rough
idle" and "low power" both pointing to "single injector
failing." But the tree forces a routing choice at the root, and
the routing choice is documented. A graph hides it.

## citations

- DDC Service Information Series 60, public-domain fault-tree
  documentation on the DDEC diagnostic logic.
- SAE J1739, "Application of Reliability Engineering to Heavy-Duty
  Diesel Engines."