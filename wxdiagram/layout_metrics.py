"""Pure layout quality metrics: edge crossings, edge length and overlaps.

No wx import.  Positions are node boxes ``(left, top, width, height)`` or
plain centre points ``(x, y)``; crossings use the straight centre-to-centre
segment as a fast layout-quality proxy for the drawn (possibly curved) edge.
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional, Tuple

from .layout import LayoutEdge


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]

_EPS = 1e-9


def _center(value) -> Point:
    """Return a centre point from ``(x, y)`` or ``(x, y, w, h)``."""
    if len(value) >= 4:
        x, y, w, h = value[:4]
        return float(x) + float(w) / 2.0, float(y) + float(h) / 2.0
    return float(value[0]), float(value[1])


def _orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_cross(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """True only for a proper crossing; touching/collinear is not counted."""
    o1 = _orientation(p1, p2, p3)
    o2 = _orientation(p1, p2, p4)
    o3 = _orientation(p3, p4, p1)
    o4 = _orientation(p3, p4, p2)
    if abs(o1) <= _EPS or abs(o2) <= _EPS or abs(o3) <= _EPS or abs(o4) <= _EPS:
        # An endpoint lying on the other segment makes this a touch, not a
        # proper crossing.  Collinear overlaps are deliberately ignored.
        return False
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def edge_endpoints(positions: Mapping[str, Box], edge: LayoutEdge) -> Optional[Tuple[Point, Point]]:
    """Return centre endpoints for an edge, or None if an endpoint is missing."""
    a = positions.get(edge.source)
    b = positions.get(edge.target)
    if a is None or b is None:
        return None
    return _center(a), _center(b)


def count_crossings(
    positions: Mapping[str, Box], edges: Iterable[LayoutEdge]
) -> int:
    """Count proper crossings between non-incident edge pairs."""
    edge_list = list(edges)
    endpoints = []
    for edge in edge_list:
        pair = edge_endpoints(positions, edge)
        if pair is not None:
            endpoints.append((edge, pair))
    count = 0
    for i in range(len(endpoints)):
        edge_a, (a1, a2) = endpoints[i]
        for j in range(i + 1, len(endpoints)):
            edge_b, (b1, b2) = endpoints[j]
            if (
                edge_a.source == edge_b.source
                or edge_a.source == edge_b.target
                or edge_a.target == edge_b.source
                or edge_a.target == edge_b.target
            ):
                continue
            if segments_cross(a1, a2, b1, b2):
                count += 1
    return count


def total_edge_length(positions: Mapping[str, Box], edges: Iterable[LayoutEdge]) -> float:
    """Sum of straight centre-to-centre lengths, ignoring missing nodes."""
    total = 0.0
    for edge in edges:
        pair = edge_endpoints(positions, edge)
        if pair is None:
            continue
        (x1, y1), (x2, y2) = pair
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return float(total)


def boxes_overlap(a: Box, b: Box, gap: float = 0.0) -> bool:
    """True when two boxes overlap or are closer than ``gap`` on both axes."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (
        ax < bx + bw + gap
        and bx < ax + aw + gap
        and ay < by + bh + gap
        and by < ay + ah + gap
    )


def boxes_from_positions(
    nodes: Iterable, positions: Mapping[str, Tuple[float, float]]
) -> Dict[str, Box]:
    """Build ``{id: (left, top, width, height)}`` from nodes and top-lefts."""
    boxes: Dict[str, Box] = {}
    for node in nodes:
        pos = positions.get(node.id)
        if pos is None:
            continue
        boxes[node.id] = (float(pos[0]), float(pos[1]), float(node.width), float(node.height))
    return boxes


__all__ = [
    "segments_cross",
    "count_crossings",
    "total_edge_length",
    "boxes_overlap",
    "boxes_from_positions",
    "edge_endpoints",
]
