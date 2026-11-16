"""Tests for the pure-math helpers in wxdiagram.geometry."""

import math

from wxdiagram import (
    GetPointOnLine,
    GetArrowPoints,
    CheckLineIntersection,
    FindEndForBox,
    FindEndForCircle,
    FindEndForPolyline,
    line_control_points_to_xy_points,
)


def test_get_point_on_line():
    x, y = GetPointOnLine(0, 0, 100, 0, 10)
    assert math.isclose(x, 90)
    assert math.isclose(y, 0)


def test_find_end_for_circle():
    # circle centre at origin radius 50; line from origin going right; intersection at x=50
    found = FindEndForCircle(50, 100, 0, 0, 0)
    assert found is not None


def test_get_arrow_points():
    pts = GetArrowPoints(0, 0, 100, 0, 20, 10)
    assert len(pts) == 6
    # the tip of the arrow is at the end of the line
    assert math.isclose(pts[0], 100)
    assert math.isclose(pts[1], 0)


def test_check_line_intersection_cross():
    ratio, k_line = CheckLineIntersection(0, 0, 100, 100, 0, 100, 100, 0)
    assert not (ratio == 1.0 and k_line == 1.0)  # (1.0, 1.0) means "no intersection"


def test_check_line_intersection_parallel_is_false():
    ratio, k_line = CheckLineIntersection(0, 0, 100, 0, 0, 10, 100, 10)
    assert ratio == 1.0 and k_line == 1.0


def test_find_end_for_box():
    pt = FindEndForBox(100, 50, 50, 25, 500, 25)
    assert pt is not None
    # ends at the right edge of the box: 100/2 = 50 from centre
    assert math.isclose(pt[0], 50 + 50, abs_tol=1)


def test_find_end_for_polyline():
    xvec = [0, 50, 100]
    yvec = [0, 50, 0]
    result = FindEndForPolyline(xvec, yvec, 150, 0, 50, 25)
    assert result is not None


def test_line_control_points_to_xy_points():
    xs, ys = line_control_points_to_xy_points([(0, 1), (20, 30), (40, 10)])
    assert xs == [0, 20, 40]
    assert ys == [1, 30, 10]
