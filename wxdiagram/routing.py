"""Pure edge routing helpers: straight, curved and orthogonal.

Kept free of wx imports so it can be tested and reused by layouts.  Callers
pass two endpoints and a list of obstacle rectangles ``(left, top, right,
bottom)``; the result is a list of control points plus a style name:

``straight``   two points, the segment is clear;
``curved``     three points, drawn as a spline through a deflected midpoint;
``orthogonal`` four points, a lane outside the obstacles.

The router deliberately stays simple (no lane occupancy or A*): enough to keep
an edge out of unrelated boxes while remaining predictable.
"""

import math

#: Extra clearance around obstacles, in diagram units.
ROUTE_PADDING = 4.0
#: How far a curved route bulges away from the straight line.
ROUTE_BEND = 48.0
#: Samples used to test a quadratic curve against obstacles.
CURVE_SAMPLES = 16
#: Short perpendicular stub before an orthogonal route turns, so it does not
#: run along the shape's own side.
ORTHOGONAL_STUB = 10.0


def segment_intersects_rect(p1, p2, rect, padding=0.0):
    """True if the segment ``p1``-``p2`` crosses ``(left, top, right, bottom)``.

    Liang-Barsky clipping; ``padding`` grows the rectangle on every side.
    """
    x1, y1 = p1
    x2, y2 = p2
    left, top, right, bottom = rect
    left -= padding
    top -= padding
    right += padding
    bottom += padding

    dx = x2 - x1
    dy = y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - left), (dx, right - x1), (-dy, y1 - top), (dy, bottom - y1)):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return False
                if r < t1:
                    t1 = r
    return True


def _polyline_clear(points, obstacles, padding):
    for first, second in zip(points, points[1:]):
        for rect in obstacles:
            if segment_intersects_rect(first, second, rect, padding):
                return False
    return True


def _quadratic(p1, control, p2, steps=CURVE_SAMPLES):
    points = []
    for step in range(steps + 1):
        t = step / steps
        inv = 1.0 - t
        points.append(
            (
                inv * inv * p1[0] + 2 * inv * t * control[0] + t * t * p2[0],
                inv * inv * p1[1] + 2 * inv * t * control[1] + t * t * p2[1],
            )
        )
    return points


def route_edge(
    p1,
    p2,
    obstacles,
    padding=ROUTE_PADDING,
    bend=ROUTE_BEND,
    spread=0.0,
    prefer_curve=False,
    prefer_orthogonal=False,
    start_normal=None,
    end_normal=None,
):
    """Route an edge from ``p1`` to ``p2`` avoiding ``obstacles``.

    Returns ``(points, style)`` where style is ``straight``, ``curved`` or
    ``orthogonal``.  Falls back to the straight segment if nothing clears.

    ``prefer_curve`` asks for a free bezier even when the straight segment is
    clear (the usual look for UML class edges); ``prefer_orthogonal`` skips the
    straight/curve tiers and goes straight to an orthogonal L/Z route.  Otherwise
    a clear segment stays straight and curves are only used to dodge boxes.

    Orthogonal routing is *only* used when ``prefer_orthogonal`` is set: the
    "auto" mode (straight or curved) never produces right-angle detours.

    ``spread`` shifts the route sideways (perpendicular to the edge) so parallel
    edges between the same pair of shapes do not overlap.  For a straight edge
    both endpoints move (along the shape sides); for the other styles only the
    interior points move, keeping the perimeter attachment exact.

    ``start_normal`` / ``end_normal`` are the outward side normals at the two
    endpoints (used by the orthogonal fallback so the edge leaves perpendicular
    to the shape side instead of running along it).
    """
    p1 = (float(p1[0]), float(p1[1]))
    p2 = (float(p2[0]), float(p2[1]))

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return [p1, p2], "straight"

    # Perpendicular to the edge, used to bulge curves and pick lanes.
    perp = (-dy / length, dx / length)
    mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    # Bow away from both boxes when we know the attachment sides (better
    # tangents than a chord-perpendicular bow for facing/opposing sides).
    bow = perp
    if start_normal and end_normal:
        normal_x = start_normal[0] + end_normal[0]
        normal_y = start_normal[1] + end_normal[1]
        normal_length = math.hypot(normal_x, normal_y)
        if normal_length > 0.5:
            bow = (normal_x / normal_length, normal_y / normal_length)

    def spread_points(points, style):
        if not spread:
            return points
        if style == "straight":
            return [(x + perp[0] * spread, y + perp[1] * spread) for x, y in points]
        return (
            [points[0]]
            + [(x + perp[0] * spread, y + perp[1] * spread) for x, y in points[1:-1]]
            + [points[-1]]
        )

    if (
        not prefer_curve
        and not prefer_orthogonal
        and (not obstacles or _polyline_clear([p1, p2], obstacles, padding))
    ):
        return spread_points([p1, p2], "straight"), "straight"

    # A gentle free curve first when the caller wants curved edges; the larger
    # deflections then act as obstacle avoidance.
    distances = []
    if prefer_curve:
        distances.append(min(bend, max(12.0, length * 0.25)))
    distances.extend((bend, bend * 2.0, bend * 3.0))

    seen = set()
    best_curve = None
    for distance in distances if not prefer_orthogonal else ():
        if distance in seen:
            continue
        seen.add(distance)
        for sign in (1.0, -1.0):
            # The returned middle point is *on* the drawn spline; convert it to
            # a quadratic Bezier control point for the clearance test.
            on_curve = (
                mid[0] + bow[0] * distance * sign,
                mid[1] + bow[1] * distance * sign,
            )
            control = (
                2.0 * on_curve[0] - mid[0],
                2.0 * on_curve[1] - mid[1],
            )
            points = [p1, on_curve, p2]
            if not obstacles or _polyline_clear(_quadratic(p1, control, p2), obstacles, padding):
                return spread_points(points, "curved"), "curved"
            best_curve = points  # last/largest deflection: best effort

    if best_curve is not None:
        # No clear curve, and auto/curved must not fall back to orthogonal.
        return spread_points(best_curve, "curved"), "curved"

    # Orthogonal fallback.  Leave each shape along its attachment normal for a
    # short stub, so the edge never runs along the box side, then pick the
    # shortest clear L/Z route whose lanes sit just outside the obstacles.
    stub = ORTHOGONAL_STUB
    s = (p1[0] + start_normal[0] * stub, p1[1] + start_normal[1] * stub) if start_normal else p1
    e = (p2[0] + end_normal[0] * stub, p2[1] + end_normal[1] * stub) if end_normal else p2
    mid_x = (s[0] + e[0]) / 2.0
    mid_y = (s[1] + e[1]) / 2.0
    lane_x = {mid_x}
    lane_y = {mid_y}
    for left, top, right, bottom in obstacles:
        lane_x.update((left - padding - 1.0, right + padding + 1.0))
        lane_y.update((top - padding - 1.0, bottom + padding + 1.0))

    candidates = []
    for x in lane_x:
        candidates.append([s, (x, s[1]), (x, e[1]), e])
    for y in lane_y:
        candidates.append([s, (s[0], y), (e[0], y), e])
    candidates.append([s, (e[0], s[1]), e])
    candidates.append([s, (s[0], e[1]), e])

    best = None
    best_length = None
    for points in candidates:
        if not _polyline_clear(points, obstacles, padding):
            continue
        length = sum(
            math.hypot(second[0] - first[0], second[1] - first[1])
            for first, second in zip(points, points[1:])
        )
        if best_length is None or length < best_length:
            best = points
            best_length = length

    if best is not None:
        full = []
        for point in [p1] + best + [p2]:
            if not full or point != full[-1]:
                full.append(point)
        return spread_points(full, "orthogonal"), "orthogonal"

    return spread_points([p1, p2], "straight"), "straight"


__all__ = [
    "route_edge",
    "segment_intersects_rect",
    "ROUTE_BEND",
    "ROUTE_PADDING",
    "ORTHOGONAL_STUB",
]
