"""Pure layout metrics: crossings, edge length and overlap helpers."""

from wxdiagram.layout import LayoutEdge, LayoutNode
from wxdiagram.layout_metrics import (
    boxes_from_positions,
    boxes_overlap,
    count_crossings,
    segments_cross,
    total_edge_length,
)


def test_segments_cross_proper_only():
    assert segments_cross((0, 0), (10, 10), (0, 10), (10, 0))
    # shared endpoint and collinear overlap are not crossings
    assert not segments_cross((0, 0), (10, 10), (10, 10), (20, 0))
    assert not segments_cross((0, 0), (10, 0), (5, 0), (15, 0))
    assert not segments_cross((0, 0), (10, 0), (0, 5), (10, 5))


def test_count_crossings():
    nodes = [LayoutNode(str(i), 20, 20) for i in range(4)]
    positions = {"0": (0, 0), "1": (90, 0), "2": (70, -20), "3": (70, 20)}
    edges = [LayoutEdge("0", "1"), LayoutEdge("2", "3")]
    boxes = boxes_from_positions(nodes, positions)
    assert count_crossings(boxes, edges) == 1
    # shared endpoints do not count
    triangle = [LayoutEdge("0", "1"), LayoutEdge("1", "2")]
    assert count_crossings(boxes, triangle) == 0


def test_total_edge_length_and_missing_nodes():
    nodes = [LayoutNode("a", 10, 10), LayoutNode("b", 10, 10)]
    positions = {"a": (0, 0), "b": (30, 40)}
    edges = [LayoutEdge("a", "b"), LayoutEdge("a", "missing")]
    boxes = boxes_from_positions(nodes, positions)
    assert total_edge_length(boxes, edges) == 50.0


def test_boxes_overlap_gap():
    assert boxes_overlap((0, 0, 10, 10), (5, 5, 10, 10))
    assert not boxes_overlap((0, 0, 10, 10), (20, 0, 10, 10))
    assert boxes_overlap((0, 0, 10, 10), (19, 0, 10, 10), gap=10)
