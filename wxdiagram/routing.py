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


def route_edge(p1, p2, obstacles, padding=ROUTE_PADDING, bend=ROUTE_BEND, spread=0.0):
    """Route an edge from ``p1`` to ``p2`` avoiding ``obstacles``.

    Returns ``(points, style)`` where style is ``straight``, ``curved`` or
    ``orthogonal``.  Falls back to the straight segment if nothing clears.

    ``spread`` shifts the route sideways (perpendicular to the edge) so parallel
    edges between the same pair of shapes do not overlap.  For a straight edge
    both endpoints move (along the shape sides); for the other styles only the
    interior points move, keeping the perimeter attachment exact.
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

    if not obstacles or _polyline_clear([p1, p2], obstacles, padding):
        return spread_points([p1, p2], "straight"), "straight"

    for distance in (bend, bend * 2.0, bend * 3.0):
        for sign in (1.0, -1.0):
            # The returned middle point is *on* the drawn spline; convert it to
            # a quadratic Bezier control point for the clearance test.
            on_curve = (
                mid[0] + perp[0] * distance * sign,
                mid[1] + perp[1] * distance * sign,
            )
            control = (
                2.0 * on_curve[0] - mid[0],
                2.0 * on_curve[1] - mid[1],
            )
            if _polyline_clear(_quadratic(p1, control, p2), obstacles, padding):
                return spread_points([p1, on_curve, p2], "curved"), "curved"

    # Orthogonal fallback: an L-ish route through a clear lane.
    horizontal = abs(dx) >= abs(dy)
    for distance in (bend, bend * 2.0, bend * 3.0, bend * 4.0):
        for sign in (1.0, -1.0):
            if horizontal:
                lane_y = mid[1] + distance * sign
                points = [p1, (p1[0], lane_y), (p2[0], lane_y), p2]
            else:
                lane_x = mid[0] + distance * sign
                points = [p1, (lane_x, p1[1]), (lane_x, p2[1]), p2]
            if _polyline_clear(points, obstacles, padding):
                return spread_points(points, "orthogonal"), "orthogonal"

    return spread_points([p1, p2], "straight"), "straight"


__all__ = ["route_edge", "segment_intersects_rect", "ROUTE_BEND", "ROUTE_PADDING"]
