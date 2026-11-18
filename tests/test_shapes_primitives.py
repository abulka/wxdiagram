"""Tests for the shape-editor primitives (colour API, ellipse/polygon fixes, groups)."""

import wx

import wxdiagram
from wxdiagram.composite import GroupShape
from wxdiagram.core import CircleShape


def _make_canvas(wx_app, size=(900, 700)):
    frame = wx.Frame(None, size=size)
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def test_fill_and_pen_colour_api(wx_app):
    shape = wxdiagram.RectangleShape(0, 0, 100, 50)
    shape.SetFillColour("#ff0000")
    fill = shape.GetFillColour()
    assert (fill.Red(), fill.Green(), fill.Blue()) == (255, 0, 0)
    shape.SetPenColour("BLUE")
    pen = shape.GetPenColour()
    assert pen.Blue() > 200
    shape.SetPenWidth(5)
    assert shape.GetPenWidth() == 5
    assert shape._pen.GetWidth() == 5


def test_shape_name_defaults_empty(wx_app):
    shape = wxdiagram.RectangleShape(0, 0, 10, 10)
    assert shape.GetName() == ""
    shape.SetName("Rectangle 1")
    assert shape.GetName() == "Rectangle 1"
    assert shape.name == "Rectangle 1"


def test_ellipse_hit_test_is_elliptical(wx_app):
    ellipse = wxdiagram.ConnectableEllipseShape()
    ellipse.x = [100, 300]
    ellipse.y = [100, 200]
    # Corners of the bounding box are outside a true ellipse.
    assert not ellipse.HitTest(101, 101)
    assert ellipse.HitTest(200, 150)


def test_ellipse_perimeter_point_lies_on_ellipse(wx_app):
    ellipse = wxdiagram.ConnectableEllipseShape()
    ellipse.x = [100, 300]
    ellipse.y = [100, 200]
    px, py = ellipse.GetPerimeterPoint(200, 150, 1000, 150)
    # Rightmost point of the ellipse is (300, 150).
    assert abs(px - 300) < 1.0
    assert abs(py - 150) < 1.0


def test_join_shapes_with_ellipse_does_not_crash(wx_app):
    frame, canvas = _make_canvas(wx_app)
    left = wxdiagram.RectangleShape(50, 100, 150, 160)
    right = wxdiagram.ConnectableEllipseShape()
    right.x = [300, 420]
    right.y = [100, 180]
    canvas.AddShape(left)
    canvas.AddShape(right)
    edge = canvas.join_shapes(left, right)
    assert edge is not None
    ends = edge.FindLineEndPoints()
    assert ends is not None and len(ends) == 4
    frame.Destroy()


def test_connectable_ellipse_and_circle_get_four_corner_handles(wx_app):
    frame, canvas = _make_canvas(wx_app)
    ellipse = wxdiagram.ConnectableEllipseShape()
    canvas.AddShape(ellipse)
    canvas.select(ellipse)
    from wxdiagram.core import ResizeableNode

    ellipse_handles = [n for n in canvas.nodes if isinstance(n, ResizeableNode)]
    assert len(ellipse_handles) == 4
    canvas.deselect()

    circle = CircleShape(10, 10, 80)
    canvas.AddShape(circle)
    canvas.select(circle)
    circle_handles = [n for n in canvas.nodes if isinstance(n, ResizeableNode)]
    assert len(circle_handles) == 4
    frame.Destroy()


def test_circle_resize_stays_square(wx_app):
    from wxdiagram.core import resize_rect_from_handle

    circle = CircleShape(0, 0, 100)
    # Drag the bottom-right corner by an uneven delta; width/height stay equal.
    resize_rect_from_handle(circle, 1, 40, 10, free_aspect=False, from_center=False)
    w = abs(circle.x[1] - circle.x[0])
    h = abs(circle.y[1] - circle.y[0])
    assert abs(w - h) < 1e-6
    assert w > 100


def test_polygon_bbox_and_centre(wx_app):
    poly = wxdiagram.PolygonShape()
    poly.Create([(0, 0), (40, 0), (20, 40)])
    assert poly.GetBoundingBoxMin() == (40, 40)
    assert poly.GetX() == 20
    assert poly.GetY() == 20


def test_zero_length_line_hit_tests_are_safe(wx_app):
    from wxdiagram.core import LineShapeBase

    line = LineShapeBase()
    assert line.HitTest(0, 0)
    assert not line.HitTest(60, 60)

    polyline = wxdiagram.LinesShape([(10, 10), (10, 10)])
    assert polyline.HitTest(10, 10)
    assert not polyline.HitTest(100, 100)


def test_moving_ellipse_target_updates_attached_edge(wx_app):
    frame, canvas = _make_canvas(wx_app)
    source = wxdiagram.Block()
    source.x, source.y = [50, 150], [100, 200]
    target = wxdiagram.ConnectableEllipseShape()
    target.x, target.y = [400, 520], [150, 250]
    canvas.InsertShape(source, 0)
    canvas.InsertShape(target, 0)
    line = canvas.join_shapes(source, target)
    line.OnMoveLink(None)
    before = line.GetEnds()
    target.move(80, 60)
    target.MoveLinks(None)
    after = line.GetEnds()
    assert abs(after[2] - before[2]) > 10 or abs(after[3] - before[3]) > 10
    frame.Destroy()


def test_moving_triangle_target_updates_attached_edge(wx_app):
    from wxdiagram.shapesdemo import DemoTriangle

    frame, canvas = _make_canvas(wx_app)
    source = wxdiagram.Block()
    source.x, source.y = [50, 150], [100, 200]
    target = DemoTriangle([(400, 200), (520, 320), (380, 320)])
    canvas.InsertShape(source, 0)
    canvas.InsertShape(target, 0)
    line = canvas.join_shapes(source, target)
    line.OnMoveLink(None)
    before = line.GetEnds()
    target.move(60, 40)
    target.MoveLinks(None)
    after = line.GetEnds()
    assert abs(after[2] - before[2]) > 10 or abs(after[3] - before[3]) > 10
    frame.Destroy()


def test_polygon_perimeter_and_scale(wx_app):
    poly = wxdiagram.PolygonShape()
    poly.Create([(0, 0), (100, 0), (50, 100)])
    px, py = poly.GetPerimeterPoint(50, 33, 50, -1000)
    # Ray from above the triangle hits the top edge y=0.
    assert abs(py - 0) < 2.0
    poly.move_handle(1, 100, 0, free_aspect=True, from_center=False)
    w, h = poly.GetBoundingBoxMin()
    assert abs(w - 200) < 1e-6
    assert max(poly.x) - min(poly.x) == w


def test_triangle_connection_points_lie_on_edges(wx_app):
    from wxdiagram.shapesdemo import DemoTriangle

    tri = DemoTriangle([(50, 0), (100, 100), (0, 100)])
    points = tri.connection_points()
    assert points["left"] == (25.0, 50.0)
    assert points["right"] == (75.0, 50.0)
    assert points["top"] == (50.0, 0.0)
    assert points["bottom"] == (50.0, 100.0)


def test_triangle_selection_uses_bbox_corner_handles(wx_app):
    from wxdiagram.core import ResizeableNode
    from wxdiagram.shapesdemo import DemoTriangle

    frame, canvas = _make_canvas(wx_app)
    tri = DemoTriangle([(50, 0), (100, 100), (0, 100)])
    canvas.AddShape(tri)
    canvas.select(tri)
    handles = [n for n in canvas.nodes if isinstance(n, ResizeableNode)]
    assert len(handles) == 4
    points = sorted(n._handle_xy() for n in handles)
    assert points == [(0, 0), (0, 100), (100, 0), (100, 100)]
    frame.Destroy()


def test_duplicate_is_placed_on_top(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = wxdiagram.RectangleShape(0, 0, 100, 50)
    last = wxdiagram.RectangleShape(200, 0, 300, 50)
    canvas.AddShape(first)
    canvas.AddShape(last)
    canvas.select(first)
    clones = canvas.duplicate_selected(offset=(10, 10))
    assert len(clones) == 1
    assert canvas.diagram.shapes[-1] is clones[0]
    assert canvas.getSelectedShapes() == [clones[0]]
    frame.Destroy()


def test_deleting_a_shape_removes_its_edges_and_undo_restores_them(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [30, 150], [30, 150]
    b = wxdiagram.ConnectableEllipseShape()
    b.x, b.y = [400, 520], [200, 320]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 0)
    line = canvas.join_shapes(a, b)

    canvas.select(a)
    canvas.delete_selected()
    assert a not in canvas.diagram.shapes
    assert line not in canvas.diagram.shapes
    assert line not in b.GetLines()

    assert canvas.undo()
    assert a in canvas.diagram.shapes
    assert line in canvas.diagram.shapes
    assert line in a.GetLines()
    assert line in b.GetLines()
    line.OnMoveLink(None)
    before = line.GetEnds()
    b.move(50, 20)
    b.MoveLinks(None)
    after = line.GetEnds()
    assert abs(after[2] - before[2]) > 5 or abs(after[3] - before[3]) > 5
    frame.Destroy()


def test_deleting_a_selected_edge_cleans_its_endpoints(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [30, 150], [30, 150]
    b = wxdiagram.Block()
    b.x, b.y = [400, 520], [200, 320]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 0)
    line = canvas.join_shapes(a, b)

    canvas.select(line)
    canvas.delete_selected()
    assert line not in canvas.diagram.shapes
    assert line not in a.GetLines()
    assert line not in b.GetLines()

    assert canvas.undo()
    assert line in canvas.diagram.shapes
    assert line in a.GetLines()
    assert line in b.GetLines()
    frame.Destroy()


def test_group_and_ungroup(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.RectangleShape(0, 0, 100, 50)
    b = wxdiagram.RectangleShape(200, 0, 300, 50)
    canvas.AddShape(a)
    canvas.AddShape(b)
    canvas.select(a)
    canvas.select(b)
    group = canvas.group_selected()
    assert isinstance(group, GroupShape)
    assert len(canvas.diagram.shapes) == 1
    assert len(group.GetChildren()) == 2
    # Children still draw at their original spots inside the frame.
    assert min(a.x) >= min(group.x) and max(a.x) <= max(group.x)

    canvas.deselect()
    canvas.select(group)
    released = canvas.ungroup_selected()
    assert len(released) == 2
    assert len(canvas.diagram.shapes) == 2
    frame.Destroy()


def test_group_excludes_lines(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.RectangleShape(0, 0, 100, 50)
    b = wxdiagram.RectangleShape(300, 0, 400, 50)
    canvas.AddShape(a)
    canvas.AddShape(b)
    edge = canvas.join_shapes(a, b)
    canvas.deselect()
    canvas.select(a)
    canvas.select(b)
    canvas.select(edge)
    group = canvas.group_selected()
    assert group is not None
    assert edge in canvas.diagram.shapes  # lines stay top-level
    assert len(group.GetChildren()) == 2
    frame.Destroy()


def test_undo_restores_colour(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.RectangleShape(0, 0, 100, 50)
    shape.SetFillColour("WHITE")
    canvas.AddShape(shape)
    canvas.begin_undo()
    shape.SetFillColour("RED")
    canvas.commit_undo()
    assert shape.GetFillColour().Green() < 200
    assert canvas.undo()
    assert shape.GetFillColour().Green() > 200
    assert canvas.redo()
    assert shape.GetFillColour().Green() < 200
    frame.Destroy()


def test_undo_group_ungroup(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.RectangleShape(0, 0, 100, 50)
    b = wxdiagram.RectangleShape(200, 0, 300, 50)
    canvas.AddShape(a)
    canvas.AddShape(b)
    canvas.select(a)
    canvas.select(b)
    canvas.group_selected()
    assert len(canvas.diagram.shapes) == 1
    assert canvas.undo()
    assert len(canvas.diagram.shapes) == 2
    assert canvas.redo()
    assert len(canvas.diagram.shapes) == 1
    assert isinstance(canvas.diagram.shapes[0], GroupShape)
    frame.Destroy()


def test_selection_callback_fires(wx_app):
    frame, canvas = _make_canvas(wx_app)
    calls = []
    canvas.onSelectionChanged = lambda c: calls.append(len(c.getSelectedShapes()))
    shape = wxdiagram.RectangleShape(0, 0, 50, 50)
    canvas.AddShape(shape)
    canvas.select(shape)
    canvas.deselect()
    assert calls == [1, 0]
    frame.Destroy()


def test_persistence_round_trip_name_group_circle(wx_app, tmp_path):
    from wxdiagram.composite import GroupShape

    diagram = wxdiagram.Diagram()
    circle = CircleShape(10, 20, 60)
    circle.SetName("My circle")
    circle.SetFillColour("#00ff00")
    diagram.AppendShape(circle)

    group = GroupShape()
    child = wxdiagram.RectangleShape(0, 0, 40, 30)
    child.SetName("Kid")
    group.AddChild(child)
    group.CalculateSize()
    group.SetName("Group 1")
    diagram.AppendShape(group)

    path = tmp_path / "shapes.json"
    wxdiagram.persistence.save(diagram, path)
    loaded = wxdiagram.persistence.load(path)
    by_name = {}
    for shape in loaded.shapes:
        by_name[shape.GetName()] = shape
        for child_shape in getattr(shape, "_compositeChildren", []) or []:
            by_name[child_shape.GetName()] = child_shape
    assert "My circle" in by_name
    assert "Group 1" in by_name
    assert "Kid" in by_name
    assert isinstance(by_name["My circle"], CircleShape)
    assert by_name["My circle"].GetFillColour().Green() > 200
