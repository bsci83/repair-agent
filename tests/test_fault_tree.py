"""Fault-tree tests — the deterministic core.

The tree is pure data + a pure walk. We test the shape, the walk
contract, and the failure modes (KeyError on bad answers).
"""

from __future__ import annotations

import pytest

from repair_diag import fault_tree


def test_every_node_reachable_from_root():
    """A node that no path from the root reaches is dead weight."""
    seen = set()

    def dfs(node_id):
        if node_id == fault_tree.CONCLUDE or node_id in seen:
            return
        seen.add(node_id)
        node = fault_tree.NODES[node_id]
        for child_id in node.child.values():
            dfs(child_id)

    dfs(fault_tree.root_id())

    unreachable = set(fault_tree.NODES) - seen
    assert not unreachable, f"unreachable nodes: {sorted(unreachable)}"


def test_root_has_only_valid_family_children():
    """Every child of root must be a known family node, not a leaf."""
    root = fault_tree.NODES["root"]
    for answer, child_id in root.child.items():
        assert child_id in fault_tree.NODES, f"{answer!r} -> unknown {child_id}"
        node = fault_tree.NODES[child_id]
        assert node.child, f"family node {child_id!r} has no children"


def test_walk_returns_path_and_conclusion():
    path, conclusion = fault_tree.walk(
        "root",
        {"root": "rough_idle", "fam_injector": "idle_and_load",
         "inj_idle_load": "black"},
    )
    assert path[0] == "root"
    assert path[-1].startswith("conclude_")
    assert "overfueling" in conclusion.lower()


def test_walk_keyerror_on_invalid_answer():
    with pytest.raises(KeyError, match="not in expected_keys"):
        fault_tree.walk(
            "root",
            {"root": "rough_idle", "fam_injector": "idle_and_load",
             "inj_idle_load": "mauve"},
        )


def test_walk_keyerror_on_unknown_node():
    with pytest.raises(KeyError):
        fault_tree.walk("no-such-node", {})


def test_walk_keyerror_on_missing_answer():
    """A node the script doesn't answer must surface as a KeyError, not
    silently fall through to a default."""
    with pytest.raises(KeyError, match="no answer given"):
        fault_tree.walk("root", {"root": "rough_idle"})


def test_all_leaves_have_conclusion_and_procedure():
    leaves = [n for n in fault_tree.NODES.values() if not n.child]
    for leaf in leaves:
        assert leaf.conclusion, f"leaf {leaf.id!r} has empty conclusion"
        assert leaf.procedure, f"leaf {leaf.id!r} has no procedure ref"


def test_safety_nodes_have_warnings_in_md():
    """Every node with a safety reference must point at a real heading."""
    for n in fault_tree.NODES.values():
        if n.safety:
            assert n.safety.startswith("safety-warnings.md#"), n.safety


def test_no_cycles():
    """The walk is a tree, not a graph. Cycles would loop forever."""
    seen: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node_id: str) -> bool:
        if node_id == fault_tree.CONCLUDE:
            return False
        if node_id in in_stack:
            return True  # cycle
        if node_id in seen:
            return False
        in_stack.add(node_id)
        node = fault_tree.NODES[node_id]
        for child in node.child.values():
            if dfs(child):
                return True
        in_stack.discard(node_id)
        seen.add(node_id)
        return False

    assert not dfs(fault_tree.root_id()), "fault tree contains a cycle"