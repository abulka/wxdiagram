"""Crossing-aware post-layout refinement."""

from wxdiagram.layout import LayoutEdge, LayoutNode
from wxdiagram.layout_refine import reduce_crossings


def _crossed_graph():
    nodes = [LayoutNode(str(i), 20, 20) for i in range(4)]
    # Edge 0-1 crosses edge 2-3; moving one of the 0/1 endpoints down removes it.
    positions = {"0": (0, 0), "1": (90, 0), "2": (70, -20), "3": (70, 20)}
    edges = [LayoutEdge("0", "1"), LayoutEdge("2", "3")]
    return nodes, edges, positions


def test_refinement_reduces_crossings():
    nodes, edges, positions = _crossed_graph()
    result = reduce_crossings(nodes, edges, positions, spacing=40)
    assert result.crossings_before == 1
    assert result.crossings_after < result.crossings_before
    assert result.moves > 0
    assert set(result.positions) == {"0", "1", "2", "3"}


def test_refinement_does_not_overlap_boxes():
    nodes, edges, positions = _crossed_graph()
    result = reduce_crossings(nodes, edges, positions, spacing=40)
    boxes = [
        (result.positions[n.id][0], result.positions[n.id][1], n.width, n.height)
        for n in nodes
    ]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax, ay, aw, ah = boxes[i]
            bx, by, bw, bh = boxes[j]
            assert ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay


def test_refinement_is_deterministic_and_honours_fixed():
    nodes, edges, positions = _crossed_graph()
    first = reduce_crossings(nodes, edges, positions, spacing=40)
    second = reduce_crossings(nodes, edges, positions, spacing=40)
    assert first.positions == second.positions

    fixed_nodes = [
        LayoutNode(n.id, n.width, n.height, n.x, n.y, fixed=(n.id == "1"))
        for n in nodes
    ]
    fixed = reduce_crossings(fixed_nodes, edges, positions, spacing=40)
    assert fixed.positions["1"] == positions["1"]


def test_no_edges_is_a_noop():
    nodes = [LayoutNode("a", 20, 20), LayoutNode("b", 20, 20)]
    positions = {"a": (0, 0), "b": (40, 0)}
    result = reduce_crossings(nodes, [], positions, spacing=40)
    assert result.positions == positions
    assert result.moves == 0
