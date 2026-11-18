"""Deterministic force-directed (spring) layout.

A clean-room port of pynsource's ``GraphLayoutSpring`` core
(``src/layout/layout_spring.py``), decoupled from ``view.graph`` and any GUI
callbacks.  Runs in an abstract force space, then maps the result to pixel
top-left positions with node-size-aware scaling and a light overlap pass.

Deterministic: pass ``seed`` (default 1) for reproducible output.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from .layout import LayoutEdge, LayoutNode, LayoutResult, register_layout
from .layout_metrics import boxes_from_positions, count_crossings, total_edge_length
from .layout_refine import reduce_crossings


class SpringLayout:
    """Fruchterman-Reingold style spring layout.

    Options: ``spacing``, ``seed``, ``iterations``, ``keep_positions``,
    ``reduce_crossings`` (default True) and ``crossing_passes``.
    ``metadata`` reports crossings and edge lengths before/after refinement.
    """

    name = "spring"

    def __init__(
        self,
        iterations: int = 500,
        k: float = 2.0,
        attraction: float = 0.01,
        max_movement: float = 0.5,
        max_repulsive_distance: float = 6.0,
        seed: int = 1,
    ):
        self.iterations = iterations
        self.k = k
        self.attraction = attraction
        self.max_movement = max_movement
        self.max_repulsive_distance = max_repulsive_distance
        self.seed = seed

    def layout(
        self,
        nodes: List[LayoutNode],
        edges: List[LayoutEdge],
        *,
        options: Optional[dict] = None,
        on_step=None,
    ) -> LayoutResult:
        opts = dict(options or {})
        iterations = int(opts.get("iterations", self.iterations))
        spacing = float(opts.get("spacing", 40.0))
        seed = opts.get("seed", self.seed)
        keep_positions = bool(opts.get("keep_positions", False))
        k = float(opts.get("k", self.k))
        attraction = float(opts.get("attraction", self.attraction))
        max_movement = float(opts.get("max_movement", self.max_movement))
        max_rep = float(opts.get("max_repulsive_distance", self.max_repulsive_distance))

        if not nodes:
            return LayoutResult(positions={}, bounds=None, metadata={"engine": "spring"})
        ids = [node.id for node in nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("SpringLayout requires unique node ids")

        rng = random.Random(seed)
        order = sorted(range(len(nodes)), key=lambda i: nodes[i].id)
        pos: Dict[str, List[float]] = {}
        force: Dict[str, List[float]] = {}
        by_id = {node.id: node for node in nodes}
        if keep_positions and all(n.x is not None and n.y is not None for n in nodes):
            # Start from current pixel positions, scaled down to force space
            # with the same per-axis scale used when mapping back.
            scale_x, scale_y = _pixel_scales(nodes, spacing, k)
            for node in nodes:
                pos[node.id] = [node.x / scale_x, node.y / scale_y]
        else:
            # Deterministic spread on a grid so components do not start stacked.
            cols = max(1, math.ceil(math.sqrt(len(order))))
            for grid_i, idx in enumerate(order):
                row, col = divmod(grid_i, cols)
                pos[nodes[idx].id] = [float(col * k * 2.0), float(row * k * 2.0)]
        for node in nodes:
            force[node.id] = [0.0, 0.0]

        snapshot = {nid: (p[0], p[1]) for nid, p in pos.items()}
        stall = 0
        for step in range(max(0, iterations)):
            # Repulsion between every pair.
            for a_i in range(len(order)):
                for b_i in range(a_i + 1, len(order)):
                    ida = nodes[order[a_i]].id
                    idb = nodes[order[b_i]].id
                    _repulse(pos, force, ida, idb, k, max_rep, rng)
            # Attraction along edges.
            seen = set()
            for edge in edges:
                if edge.source not in by_id or edge.target not in by_id:
                    continue
                if edge.source == edge.target:
                    continue  # self-loops do not pull
                key = (edge.source, edge.target, edge.weight)
                if key in seen:
                    continue
                seen.add(key)
                _attract(pos, force, edge.source, edge.target, k, max_rep, edge.weight)
            # Move (fixed nodes still exert forces but do not move).
            for node in nodes:
                if node.fixed:
                    force[node.id] = [0.0, 0.0]
                    continue
                fx, fy = force[node.id]
                dx = max(-max_movement, min(max_movement, attraction * fx))
                dy = max(-max_movement, min(max_movement, attraction * fy))
                pos[node.id][0] += dx
                pos[node.id][1] += dy
                force[node.id] = [0.0, 0.0]
            if on_step is not None:
                try:
                    keep_going = on_step(step, {"positions": dict(pos)})
                except TypeError:
                    keep_going = on_step(step)
                if keep_going is False:
                    break
            # Early stop: if the largest displacement over the last 20 steps
            # is tiny for several checks in a row, further iterations are
            # wasted.
            if step and step % 20 == 0:
                largest = 0.0
                for node in nodes:
                    if node.fixed or node.id not in snapshot:
                        continue
                    ox, oy = snapshot[node.id]
                    largest = max(largest, abs(pos[node.id][0] - ox), abs(pos[node.id][1] - oy))
                if largest < 0.05:
                    stall += 1
                    if stall >= 3:
                        break
                else:
                    stall = 0
                snapshot = {nid: (p[0], p[1]) for nid, p in pos.items()}

        pixel = _to_pixels(nodes, pos, spacing, k)
        pixel = _pack_components(nodes, edges, pixel, spacing)
        _separate_overlaps(nodes, pixel, spacing, passes=8)
        positions = {nid: (float(p[0]), float(p[1])) for nid, p in pixel.items()}
        boxes = boxes_from_positions(nodes, positions)
        crossings_before = count_crossings(boxes, edges)
        length_before = total_edge_length(boxes, edges)
        refinement_moves = 0
        if bool(opts.get("reduce_crossings", True)) and edges:
            refined = reduce_crossings(
                nodes,
                edges,
                positions,
                spacing=spacing,
                passes=int(opts.get("crossing_passes", 4)),
            )
            positions = refined.positions
            refinement_moves = refined.moves
            boxes = boxes_from_positions(nodes, positions)
        crossings_after = count_crossings(boxes, edges)
        length_after = total_edge_length(boxes, edges)
        lefts = [positions[n.id][0] for n in nodes]
        tops = [positions[n.id][1] for n in nodes]
        rights = [positions[n.id][0] + n.width for n in nodes]
        bottoms = [positions[n.id][1] + n.height for n in nodes]
        bounds = (min(lefts), min(tops), max(rights), max(bottoms))
        return LayoutResult(
            positions=positions,
            bounds=bounds,
            metadata={
                "engine": "spring",
                "iterations": iterations,
                "seed": seed,
                "crossings": crossings_after,
                "crossings_before": crossings_before,
                "refinement_moves": refinement_moves,
                "edge_length": length_after,
                "edge_length_before": length_before,
            },
        )


def _repulse(pos, force, ida, idb, k, max_rep, rng):
    ax, ay = pos[ida]
    bx, by = pos[idb]
    dx, dy = bx - ax, by - ay
    d2 = dx * dx + dy * dy
    if d2 < 0.01:
        dx = 0.1 * rng.random() + 0.1
        dy = 0.1 * rng.random() + 0.1
        d2 = dx * dx + dy * dy
    d = math.sqrt(d2)
    if d < max_rep:
        f = k * k / d
        ux, uy = dx / d, dy / d
        force[idb][0] += f * ux
        force[idb][1] += f * uy
        force[ida][0] -= f * ux
        force[ida][1] -= f * uy


def _attract(pos, force, ida, idb, k, max_rep, weight):
    ax, ay = pos[ida]
    bx, by = pos[idb]
    dx, dy = bx - ax, by - ay
    d2 = dx * dx + dy * dy
    if d2 < 1e-9:
        return
    d = math.sqrt(d2)
    dc = min(d, max_rep)
    f = (dc * dc - k * k) / k
    try:
        w = float(weight)
    except (TypeError, ValueError):
        w = 1.0
    if not w or w < 1:
        w = 1.0
    f *= math.log(w) * 0.5 + 1
    ux, uy = dx / d, dy / d
    force[idb][0] -= f * ux
    force[idb][1] -= f * uy
    force[ida][0] += f * ux
    force[ida][1] += f * uy


def _pixel_scales(nodes: List[LayoutNode], spacing: float, k: float) -> Tuple[float, float]:
    avg_w = sum(n.width for n in nodes) / len(nodes)
    avg_h = sum(n.height for n in nodes) / len(nodes)
    scale_x = (avg_w + spacing * 2.0) / max(k, 1e-6)
    scale_y = (avg_h + spacing * 2.0) / max(k, 1e-6)
    return max(scale_x, 1.0), max(scale_y, 1.0)


def _to_pixels(nodes, pos, spacing, k) -> Dict[str, List[float]]:
    xs = [pos[n.id][0] for n in nodes]
    ys = [pos[n.id][1] for n in nodes]
    min_x, min_y = min(xs), min(ys)
    scale_x, scale_y = _pixel_scales(nodes, spacing, k)
    margin = max(spacing, 20.0)
    out: Dict[str, List[float]] = {}
    for node in nodes:
        if node.fixed and node.x is not None and node.y is not None:
            out[node.id] = [float(node.x), float(node.y)]
            continue
        px = (pos[node.id][0] - min_x) * scale_x + margin
        py = (pos[node.id][1] - min_y) * scale_y + margin
        out[node.id] = [px, py]
    return out


def _components(nodes, edges) -> List[List[str]]:
    parent = {n.id: n.id for n in nodes}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    ids = set(parent)
    for edge in edges:
        if edge.source in ids and edge.target in ids:
            union(edge.source, edge.target)
    groups: Dict[str, List[str]] = {}
    for nid in ids:
        groups.setdefault(find(nid), []).append(nid)
    return [sorted(g) for g in sorted(groups.values(), key=lambda g: g[0])]


def _pack_components(nodes, edges, pixel, spacing) -> Dict[str, List[float]]:
    """Shift disconnected components into a non-overlapping grid."""
    if any(node.fixed for node in nodes):
        # Pinned nodes already define absolute positions; component packing
        # would move their neighbours away.  Overlap separation still runs.
        return pixel
    by_id = {n.id: n for n in nodes}
    comps = _components(nodes, edges)
    if len(comps) <= 1:
        return pixel
    boxes = []
    for comp in comps:
        xs = [pixel[nid][0] for nid in comp]
        ys = [pixel[nid][1] for nid in comp]
        rs = [pixel[nid][0] + by_id[nid].width for nid in comp]
        bs = [pixel[nid][1] + by_id[nid].height for nid in comp]
        boxes.append((min(xs), min(ys), max(rs), max(bs), comp))
    boxes.sort(key=lambda b: (b[1], b[0]))
    row_start_x = min(b[0] for b in boxes)
    row_y = min(b[1] for b in boxes)
    row_h = 0.0
    cursor_x = row_start_x
    gap = max(spacing, 20.0)
    max_row_width = max(1200.0, gap * 20.0)
    placed: Dict[str, List[float]] = dict(pixel)
    for left, top, right, bottom, comp in boxes:
        w, h = right - left, bottom - top
        if cursor_x > row_start_x and cursor_x - row_start_x + w > max_row_width:
            cursor_x = row_start_x
            row_y += row_h + gap
            row_h = 0.0
        dx = cursor_x - left
        dy = row_y - top
        for nid in comp:
            # Fixed nodes stay where the user put them.
            if by_id[nid].fixed:
                continue
            placed[nid] = [pixel[nid][0] + dx, pixel[nid][1] + dy]
        cursor_x += w + gap
        row_h = max(row_h, h)
    return placed


def _overlaps(a_box, b_box, gap: float) -> Tuple[float, float] | None:
    ax, ay, aw, ah = a_box
    bx, by, bw, bh = b_box
    dx = (ax + aw / 2) - (bx + bw / 2)
    dy = (ay + ah / 2) - (by + bh / 2)
    ox = (aw + bw) / 2 + gap - abs(dx)
    oy = (ah + bh) / 2 + gap - abs(dy)
    if ox > 0 and oy > 0:
        return ox, oy
    return None


def _separate_overlaps(nodes, pixel, spacing, passes=8):
    by_id = {n.id: n for n in nodes}
    gap = max(float(spacing) / 2.0, 8.0)
    ids = [n.id for n in nodes]
    for _ in range(passes):
        moved = False
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                na, nb = by_id[a], by_id[b]
                abox = (pixel[a][0], pixel[a][1], na.width, na.height)
                bbox = (pixel[b][0], pixel[b][1], nb.width, nb.height)
                ov = _overlaps(abox, bbox, gap)
                if not ov:
                    continue
                ox, oy = ov
                a_fixed, b_fixed = na.fixed, nb.fixed
                if a_fixed and b_fixed:
                    continue
                if ox < oy:
                    shift = ox / 2.0
                    sign = 1.0 if pixel[a][0] >= pixel[b][0] else -1.0
                    if not a_fixed:
                        pixel[a][0] += sign * (shift if not b_fixed else shift * 2)
                    if not b_fixed:
                        pixel[b][0] -= sign * (shift if not a_fixed else shift * 2)
                else:
                    shift = oy / 2.0
                    sign = 1.0 if pixel[a][1] >= pixel[b][1] else -1.0
                    if not a_fixed:
                        pixel[a][1] += sign * (shift if not b_fixed else shift * 2)
                    if not b_fixed:
                        pixel[b][1] -= sign * (shift if not a_fixed else shift * 2)
                moved = True
        if not moved:
            break


register_layout(SpringLayout)


__all__ = ["SpringLayout"]
