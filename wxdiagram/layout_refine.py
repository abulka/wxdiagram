"""Deterministic post-layout refinement that reduces edge crossings.

Layout engines decide where boxes go; this pass nudges *movable* boxes to
positions that cross fewer edges.  It is a local search, not a global
optimiser: crossings that require a different graph embedding cannot be
removed, and fixed nodes never move.

Pure Python (no wx import).  Positions are top-left ``(x, y)``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from .layout import LayoutEdge, LayoutNode
from .layout_metrics import (
    boxes_from_positions,
    boxes_overlap,
    count_crossings,
    segments_cross,
    total_edge_length,
)


_DIRECTIONS = (
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
    (1.0, 1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
    (-1.0, -1.0),
)


@dataclass
class RefineResult:
    """Refined top-left positions plus before/after quality statistics."""

    positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    crossings_before: int = 0
    crossings_after: int = 0
    edge_length_before: float = 0.0
    edge_length_after: float = 0.0
    moves: int = 0


def reduce_crossings(
    nodes: List[LayoutNode],
    edges: List[LayoutEdge],
    positions: Mapping[str, Tuple[float, float]],
    *,
    spacing: float = 40.0,
    passes: int = 4,
    step: Optional[float] = None,
    min_step: Optional[float] = None,
) -> RefineResult:
    """Move non-fixed nodes to reduce crossings, then return the new layout.

    ``spacing`` controls the clearance kept between boxes and the default
    search step.  The search is deterministic: nodes are visited in sorted-id
    order and candidates in a fixed direction order.
    """
    boxes = boxes_from_positions(nodes, positions)
    base_positions = {nid: (float(p[0]), float(p[1])) for nid, p in positions.items()}
    if len(boxes) < 2 or not edges:
        return RefineResult(
            positions=base_positions,
            crossings_before=count_crossings(boxes, edges),
            crossings_after=count_crossings(boxes, edges),
            edge_length_before=total_edge_length(boxes, edges),
            edge_length_after=total_edge_length(boxes, edges),
        )

    before_boxes = {nid: tuple(box) for nid, box in boxes.items()}
    before_crossings = count_crossings(before_boxes, edges)
    before_length = total_edge_length(before_boxes, edges)
    if len(nodes) * len(edges) > 20000:
        return RefineResult(
            positions=base_positions,
            crossings_before=before_crossings,
            crossings_after=before_crossings,
            edge_length_before=before_length,
            edge_length_after=before_length,
        )

    clearance = max(float(spacing) / 2.0, 4.0)
    current_step = float(step) if step is not None else max(float(spacing), 24.0)
    floor = float(min_step) if min_step is not None else max(current_step / 4.0, 4.0)
    ordered = [node for node in sorted(nodes, key=lambda n: n.id) if node.id in boxes]
    moves = 0
    sweeps = 0

    while current_step >= floor and sweeps < max(1, int(passes)):
        moved_this_sweep = False
        for node in ordered:
            if node.fixed:
                continue
            box = boxes[node.id]
            candidates = _candidate_centers(node, box, boxes, edges, current_step)
            best = _best_candidate(node, box, candidates, boxes, edges, clearance)
            if best is None:
                continue
            new_center, delta_cross, delta_len = best
            if delta_cross > 0 or (delta_cross == 0 and delta_len >= -1e-6):
                continue
            boxes[node.id] = (
                new_center[0] - node.width / 2.0,
                new_center[1] - node.height / 2.0,
                node.width,
                node.height,
            )
            moved_this_sweep = True
            moves += 1
        sweeps += 1
        if not moved_this_sweep:
            current_step /= 2.0

    refined = {
        nid: (float(box[0]), float(box[1])) for nid, box in boxes.items()
    }
    return RefineResult(
        positions=refined,
        crossings_before=before_crossings,
        crossings_after=count_crossings(boxes, edges),
        edge_length_before=before_length,
        edge_length_after=total_edge_length(boxes, edges),
        moves=moves,
    )


def _candidate_centers(
    node: LayoutNode,
    box: Tuple[float, float, float, float],
    boxes: Mapping[str, Tuple[float, float, float, float]],
    edges: List[LayoutEdge],
    step: float,
) -> List[Tuple[float, float]]:
    cx = box[0] + node.width / 2.0
    cy = box[1] + node.height / 2.0
    seen = {(round(cx, 6), round(cy, 6))}
    candidates: List[Tuple[float, float]] = []

    def add(x: float, y: float):
        key = (round(x, 6), round(y, 6))
        if key not in seen:
            seen.add(key)
            candidates.append((x, y))

    for dx, dy in _DIRECTIONS:
        length = math.hypot(dx, dy)
        add(cx + dx / length * step, cy + dy / length * step)

    # Neighbour-aware moves: away from, and towards, adjacent boxes.
    neighbours = _neighbours(node.id, edges)
    for other_id in neighbours:
        other = boxes.get(other_id)
        if other is None:
            continue
        ox = other[0] + other[2] / 2.0
        oy = other[1] + other[3] / 2.0
        vx, vy = ox - cx, oy - cy
        length = math.hypot(vx, vy)
        if length < 1e-6:
            continue
        ux, uy = vx / length, vy / length
        add(cx + ux * step, cy + uy * step)
        add(cx - ux * step, cy - uy * step)

    if boxes:
        gx = sum(b[0] + b[2] / 2.0 for b in boxes.values()) / len(boxes)
        gy = sum(b[1] + b[3] / 2.0 for b in boxes.values()) / len(boxes)
        vx, vy = gx - cx, gy - cy
        length = math.hypot(vx, vy)
        if length > 1e-6:
            add(cx + vx / length * step, cy + vy / length * step)
    return candidates


def _neighbours(node_id: str, edges: Iterable[LayoutEdge]) -> set:
    neighbours = set()
    for edge in edges:
        if edge.source == node_id:
            neighbours.add(edge.target)
        elif edge.target == node_id:
            neighbours.add(edge.source)
    return neighbours


def _best_candidate(
    node: LayoutNode,
    box: Tuple[float, float, float, float],
    candidates: Iterable[Tuple[float, float]],
    boxes: Mapping[str, Tuple[float, float, float, float]],
    edges: List[LayoutEdge],
    clearance: float,
):
    incident, others = _incident_and_other(edges, node.id)
    if not incident:
        return None
    old_crossings = _local_crossings(incident, others, boxes, node.id)
    old_length = _local_length(incident, boxes, node.id)
    best = None
    for cx, cy in candidates:
        candidate_box = (
            cx - node.width / 2.0,
            cy - node.height / 2.0,
            node.width,
            node.height,
        )
        if any(
            other_id != node.id and boxes_overlap(candidate_box, other_box, clearance)
            for other_id, other_box in boxes.items()
        ):
            continue
        trial = dict(boxes)
        trial[node.id] = candidate_box
        crossings = _local_crossings(incident, others, trial, node.id)
        length = _local_length(incident, trial, node.id)
        score = (crossings - old_crossings, length - old_length)
        if best is None or score < best[0]:
            best = (score, (cx, cy))
    if best is None:
        return None
    (delta_cross, delta_len), center = best
    return center, delta_cross, delta_len


def _incident_and_other(edges: Iterable[LayoutEdge], node_id: str):
    incident: List[LayoutEdge] = []
    others: List[LayoutEdge] = []
    for edge in edges:
        if edge.source == node_id or edge.target == node_id:
            incident.append(edge)
        else:
            others.append(edge)
    return incident, others


def _share_endpoint(a: LayoutEdge, b: LayoutEdge) -> bool:
    return (
        a.source == b.source
        or a.source == b.target
        or a.target == b.source
        or a.target == b.target
    )


def _segment(edge: LayoutEdge, boxes):
    a = boxes.get(edge.source)
    b = boxes.get(edge.target)
    if a is None or b is None:
        return None
    return (
        (a[0] + a[2] / 2.0, a[1] + a[3] / 2.0),
        (b[0] + b[2] / 2.0, b[1] + b[3] / 2.0),
    )


def _local_crossings(incident, others, boxes, node_id) -> int:
    count = 0
    for edge in incident:
        pair = _segment(edge, boxes)
        if pair is None:
            continue
        for other in others:
            if _share_endpoint(edge, other):
                continue
            other_pair = _segment(other, boxes)
            if other_pair is None:
                continue
            if segments_cross(pair[0], pair[1], other_pair[0], other_pair[1]):
                count += 1
    return count


def _local_length(incident, boxes, node_id) -> float:
    total = 0.0
    for edge in incident:
        pair = _segment(edge, boxes)
        if pair is None:
            continue
        (x1, y1), (x2, y2) = pair
        total += math.hypot(x2 - x1, y2 - y1)
    return total


__all__ = ["RefineResult", "reduce_crossings"]
