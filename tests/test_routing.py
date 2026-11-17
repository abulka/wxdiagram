"""Edge routing: straight, curved and orthogonal fallbacks."""

import wx

import pytest

import wxdiagram
from wxdiagram.routing import route_edge, segment_intersects_rect, _quadratic


def test_segment_intersects_rect():
    assert segment_intersects_rect((0, 0), (100, 0), (40, -10, 60, 10))
    assert not segment_intersects_rect((0, 0), (100, 0), (40, 10, 60, 20))
    # padding makes a near miss count as a hit
    assert segment_intersects_rect((0, 0), (100, 0), (40, 5, 60, 20), padding=5)


def test_straight_when_clear():
    points, style = route_edge((0, 0), (200, 0), [(0, 100, 50, 140)])

    assert style == "straight"
    assert points == [(0.0, 0.0), (200.0, 0.0)]


def test_curved_route_clears_the_obstacle():
    obstacle = (80, -30, 120, 30)
    points, style = route_edge((0, 0), (200, 0), [obstacle])

    assert style == "curved"
    assert len(points) == 3
    assert points[1][1] != 0  # deflected off the straight line

    # The drawn spline passes through points[1]; the equivalent quadratic
    # control point is 2*D - mid.
    mid = (100.0, 0.0)
    control = (2 * points[1][0] - mid[0], 2 * points[1][1] - mid[1])
    sampled = _quadratic(points[0], control, points[2])
    for first, second in zip(sampled, sampled[1:]):
        assert not segment_intersects_rect(first, second, obstacle, padding=4)


def test_orthogonal_fallback_when_curves_are_blocked():
    # A tall wall blocks the straight line and every curve deflection.
    obstacle = (80, -150, 120, 150)
    points, style = route_edge((0, 0), (200, 0), [obstacle])

    assert style == "orthogonal"
    assert len(points) == 4
    for first, second in zip(points, points[1:]):
        assert not segment_intersects_rect(first, second, obstacle, padding=4)


def test_route_avoids_every_obstacle():
    obstacles = [(40, -60, 70, 0), (40, -10, 70, 60)]
    start, end = (0, 0), (140, 0)
    points, style = route_edge(start, end, obstacles)

    assert style in ("curved", "orthogonal")
    if style == "curved":
        mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        control = (2 * points[1][0] - mid[0], 2 * points[1][1] - mid[1])
        sampled = _quadratic(start, control, end)
        segments = zip(sampled, sampled[1:])
    else:
        segments = zip(points, points[1:])
    for first, second in segments:
        for obstacle in obstacles:
            assert not segment_intersects_rect(first, second, obstacle, padding=4)


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(700, 500))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _block(left, top, right, bottom):
    block = wxdiagram.Block()
    block.x = [left, right]
    block.y = [top, bottom]
    return block


def test_autoroute_is_off_by_default(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = _block(0, 0, 80, 60)
    b = _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)

    assert line.autoRoute is False
    line.OnMoveLink(None)
    assert len(line._lineControlPoints) == 2
    assert not line.IsSpline()
    frame.Destroy()


def test_autoroute_goes_around_a_blocker_and_back_to_straight(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = _block(0, 0, 80, 60)
    b = _block(320, 0, 400, 60)
    blocker = wxdiagram.RectangleShape(170, -150, 230, 200)
    canvas.AddShape(a)
    canvas.AddShape(b)
    canvas.AddShape(blocker)
    line = canvas.join_shapes(a, b)
    line.autoRoute = True

    style = line.UpdateRoute()
    assert style in ("curved", "orthogonal")
    assert len(line._lineControlPoints) > 2

    # Moving the blocker out of the way restores the straight edge.
    blocker.x = [500, 540]
    blocker.y = [0, 60]
    style = line.UpdateRoute()
    assert style == "straight"
    assert len(line._lineControlPoints) == 2
    assert not line.IsSpline()
    frame.Destroy()


def test_autoroute_survives_repeated_link_updates(wx_app):
    """Routing must not drift when both shapes keep moving."""
    frame, canvas = _make_canvas(wx_app)
    a = _block(0, 0, 80, 60)
    b = _block(320, 0, 400, 60)
    blocker = wxdiagram.RectangleShape(170, -150, 230, 200)
    canvas.AddShape(a)
    canvas.AddShape(b)
    canvas.AddShape(blocker)
    line = canvas.join_shapes(a, b)
    line.autoRoute = True

    line.UpdateRoute()
    first = [(p[0], p[1]) for p in line._lineControlPoints]
    for _ in range(3):
        a.MoveLinks(None)
        b.MoveLinks(None)
        line.OnMoveLink(None)
    second = [(p[0], p[1]) for p in line._lineControlPoints]

    assert first == second
    frame.Destroy()


def test_parallel_edges_are_spread_apart(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = _block(0, 0, 80, 60)
    b = _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    first = canvas.join_shapes(a, b)
    second = canvas.join_shapes(a, b)
    for line in (first, second):
        line.autoRoute = True
        line.UpdateRoute()

    y1 = first._lineControlPoints[0][1]
    y2 = second._lineControlPoints[0][1]
    assert y1 != y2
    assert abs(y1 - y2) == pytest.approx(14.0)  # default lane spacing
    frame.Destroy()


def test_single_edge_has_no_lane_offset(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = _block(0, 0, 80, 60)
    b = _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    line.autoRoute = True
    line.UpdateRoute()

    assert line._lane_offset() == 0.0
    assert line._lineControlPoints[0][1] == pytest.approx(30.0)
    frame.Destroy()
