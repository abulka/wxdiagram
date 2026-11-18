"""Regression tests for the mouse/painting bugs reported against the demo."""

import wx

import pytest

import wxdiagram
from wxdiagram.composite import CompositeShape
from wxdiagram.core import ConnectionHandleNode, INode, ONode, ResizeableNode


def _make_canvas(wx_app, size=(800, 600)):
    frame = wx.Frame(None, size=size)
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _event(canvas, wx_type, client_xy):
    evt = wx.MouseEvent(wx_type)
    evt.SetPosition(wx.Point(int(client_xy[0]), int(client_xy[1])))
    evt.SetX(int(client_xy[0]))
    evt.SetY(int(client_xy[1]))
    evt.SetEventObject(canvas)
    return evt


def _click(canvas, diagram_xy):
    """Click at a diagram coordinate, using the canvas's own transforms."""
    client = canvas.diagram_point_to_client_coords(*diagram_xy)
    canvas.GetEventHandler().ProcessEvent(_event(canvas, wx.wxEVT_LEFT_DOWN, client))
    canvas.GetEventHandler().ProcessEvent(_event(canvas, wx.wxEVT_LEFT_UP, client))
    wx.Yield()


def _mock_dc():
    class RecordingDC:
        def __init__(self):
            self.calls = []

        def __getattr__(self, name):
            def record(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                if name == "GetTextExtent":
                    return (40, 12)
                return None

            return record

    return RecordingDC()


def test_insert_shape_attaches_canvas(wx_app):
    """InsertShape was the demo's only insertion path and never set _canvas."""
    frame, canvas = _make_canvas(wx_app)
    rect = wxdiagram.RectangleShape(0, 0, 100, 50)
    canvas.InsertShape(rect, 0)
    assert rect.GetCanvas() is canvas
    frame.Destroy()


def test_composite_children_get_canvas(wx_app):
    frame, canvas = _make_canvas(wx_app)
    composite = CompositeShape()
    composite.x = [0, 200]
    composite.y = [0, 100]
    child = wxdiagram.RectangleShape(10, 10, 50, 40)
    composite.add_child(child)
    canvas.InsertShape(composite, 0)
    assert composite.GetCanvas() is canvas
    assert child.GetCanvas() is canvas
    frame.Destroy()


def test_set_diagram_attaches_loaded_shapes(wx_app, tmp_path):
    """Loading returns a Diagram that is then handed to SetDiagram."""
    frame, canvas = _make_canvas(wx_app)
    diagram = wxdiagram.Diagram()
    rect = wxdiagram.RectangleShape(10, 10, 100, 50)
    diagram.AddShape(rect)
    path = tmp_path / "diagram.json"
    diagram.Save(str(path))
    loaded = wxdiagram.Diagram.Load(str(path))
    canvas.SetDiagram(loaded)
    assert all(shape.GetCanvas() is canvas for shape in loaded.shapes)
    frame.Destroy()


def test_clicking_inserted_shape_does_not_assert(wx_app):
    """OnLeftUp used to assert shape._canvas and crash mid-click."""
    frame, canvas = _make_canvas(wx_app)
    rect = wxdiagram.RectangleShape(100, 100, 300, 200)
    canvas.InsertShape(rect, 0)
    _click(canvas, (200, 150))
    assert rect in canvas.getSelectedShapes()
    frame.Destroy()


def test_line_move_moves_control_points(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(100, 100, 300, 200)
    canvas.InsertShape(line, 0)

    line.move(10, 20)
    x1, y1, x2, y2 = line.GetEnds()
    assert (x1, y1, x2, y2) == (110, 120, 310, 220)
    frame.Destroy()


def test_dragging_selected_line_moves_it(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(100, 100, 300, 200)
    canvas.InsertShape(line, 0)
    canvas.select(line)

    class FakeMotion:
        def Dragging(self):
            return True

        def GetX(self):
            return 210

        def GetY(self):
            return 160

    # first click puts currentPoint at (200, 150)
    canvas.currentPoint = (200, 150)
    canvas.OnMotion(FakeMotion())
    x1, y1, x2, y2 = line.GetEnds()
    assert (x1, y1, x2, y2) == (110, 110, 310, 210)
    frame.Destroy()


def test_line_handle_moves_only_that_end(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(100, 100, 300, 200)
    canvas.InsertShape(line, 0)

    canvas.select(line)
    node = next(n for n in canvas.nodes if isinstance(n, ResizeableNode) and n.index == 0)
    node.move(15, 5)

    x1, y1, x2, y2 = line.GetEnds()
    assert (x1, y1) == (115, 105)
    assert (x2, y2) == (300, 200)
    frame.Destroy()


def test_clicking_line_then_shape_clears_previous_selection(wx_app):
    frame, canvas = _make_canvas(wx_app)
    rect = wxdiagram.RectangleShape(0, 0, 100, 100)
    canvas.InsertShape(rect, 0)
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(200, 200, 400, 300)
    canvas.InsertShape(line, 1)

    _click(canvas, (300, 250))  # on the line
    assert canvas.getSelectedShapes() == [line]

    _click(canvas, (50, 50))  # on the rectangle
    assert canvas.getSelectedShapes() == [rect]
    assert all(node.item is rect for node in canvas.nodes)
    frame.Destroy()


def test_resize_handles_are_hittable_before_the_first_paint(wx_app):
    """Handles are positioned when created, not only when drawn.

    Otherwise a click that arrives between select() and the next paint misses
    the handle and drags the shape instead of resizing it.
    """
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 250)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    # Deliberately no _redraw(): the demo's Refresh() is asynchronous.
    hit = canvas.shapeFromPoint((shape.x[1], shape.y[1]))
    assert isinstance(hit, ResizeableNode)
    assert hit.item is shape
    frame.Destroy()


def test_edge_handle_drag_resizes_one_axis(wx_app):
    """Edge handles drag a single axis and keep the shape selected."""
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)
    _redraw(canvas)

    _drag(canvas, (300, 150), (340, 190))  # right-edge handle

    assert shape.GetBoundingBoxMin() == (240.0, 100.0)
    assert canvas.getSelectedShapes() == [shape]
    frame.Destroy()


def _redraw(canvas):
    """Draw offscreen so nodes reposition themselves during a scripted drag."""
    dc = wx.MemoryDC(wx.Bitmap(800, 600))
    canvas.Redraw(dc)
    dc.SelectObject(wx.NullBitmap)


def _drag(canvas, start_diagram, end_diagram, steps=4):
    def evt(wx_type, diagram_xy):
        client = canvas.diagram_point_to_client_coords(*diagram_xy)
        e = _event(canvas, wx_type, client)
        if wx_type == wx.wxEVT_MOTION:
            e.SetLeftDown(True)
        return e

    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_LEFT_DOWN, start_diagram))
    _redraw(canvas)
    for i in range(1, steps + 1):
        t = i / steps
        point = (
            start_diagram[0] + (end_diagram[0] - start_diagram[0]) * t,
            start_diagram[1] + (end_diagram[1] - start_diagram[1]) * t,
        )
        canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_MOTION, point))
        _redraw(canvas)
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_LEFT_UP, end_diagram))
    wx.Yield()


def _hover(canvas, diagram_xy):
    """Move the mouse (no buttons pressed) to a diagram coordinate."""
    client = canvas.diagram_point_to_client_coords(*diagram_xy)
    e = _event(canvas, wx.wxEVT_MOTION, client)
    canvas.GetEventHandler().ProcessEvent(e)
    wx.Yield()


def _attached_lines(canvas):
    return [s for s in canvas.diagram.shapes if isinstance(s, wxdiagram.LineShape)]


def _assert_routed_between(line, from_shape, to_shape, tol=1e-6):
    """An attached edge must meet both boxes on their boundary, on the
    straight line through the two shape centres."""
    x1, y1, x2, y2 = line.GetEnds()
    assert _on_boundary(from_shape, (x1, y1), tol)
    assert _on_boundary(to_shape, (x2, y2), tol)
    assert _dist_point_to_centre_line((x1, y1), from_shape, to_shape) < tol
    assert _dist_point_to_centre_line((x2, y2), from_shape, to_shape) < tol


def _on_boundary(shape, pt, tol=1e-6):
    x, y = pt
    in_x = shape.x[0] - tol <= x <= shape.x[1] + tol
    in_y = shape.y[0] - tol <= y <= shape.y[1] + tol
    on_v = abs(x - shape.x[0]) < tol or abs(x - shape.x[1]) < tol
    on_h = abs(y - shape.y[0]) < tol or abs(y - shape.y[1]) < tol
    return in_x and in_y and (on_v or on_h)


def _dist_point_to_centre_line(pt, from_shape, to_shape):
    """Perpendicular distance from pt to the line through both centres."""
    x0, y0 = pt
    x1, y1 = from_shape.GetX(), from_shape.GetY()
    x2, y2 = to_shape.GetX(), to_shape.GetY()
    dx, dy = x2 - x1, y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5
    return abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / length


def _block(left, top, size=100):
    block = wxdiagram.Block()
    block.x = [left, left + size]
    block.y = [top, top + size]
    return block


def test_drag_from_output_port_creates_an_attached_line(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    b = wxdiagram.Block()
    b.x, b.y = [450, 550], [250, 350]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 1)

    start = a.getPort("output", 0)
    end = b.getPort("input", 0)
    _hover(canvas, start)  # ports appear as drag handles
    assert any(isinstance(n, ONode) and n.item is a for n in canvas.nodes)
    _drag(canvas, start, end)

    # the finished edge is attached, not a port-to-port ConnectionShape
    assert not any(isinstance(s, wxdiagram.ConnectionShape) for s in canvas.diagram.shapes)
    lines = _attached_lines(canvas)
    assert len(lines) == 1
    line = lines[0]
    assert line._from is a
    assert line._to is b

    # centre-to-centre routing: a(100,100) -> b(500,300) leaves a's right
    # edge at y=125, not at the fixed mid-right port (150, 100)
    x1, y1, x2, y2 = line.GetEnds()
    assert (x1, y1) == pytest.approx((150, 125))
    assert (x2, y2) == pytest.approx((450, 275))
    frame.Destroy()


def test_drag_from_dot_to_any_shape_body_creates_an_edge(wx_app):
    """Releasing over a shape body (not an exact port) completes the edge."""
    from wxdiagram.shapesdemo import DemoTriangle

    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    b = wxdiagram.ConnectableEllipseShape()
    b.x, b.y = [450, 570], [250, 350]
    tri = DemoTriangle([(700, 220), (820, 380), (580, 380)])
    for shape in (a, b, tri):
        shape.SetCanvas(canvas)
        canvas.InsertShape(shape, 0)

    # Start at a's right-hand dot and release in the middle of the ellipse.
    start = a.getPort("output", 0)
    _hover(canvas, start)
    assert any(isinstance(n, ConnectionHandleNode) for n in canvas.nodes)
    _drag(canvas, start, (b.GetX(), b.GetY()))

    lines = _attached_lines(canvas)
    assert len(lines) == 1
    assert lines[0]._from is a
    assert lines[0]._to is b

    # Same again, this time dropping on a triangle's body.
    canvas.deselect()
    _hover(canvas, start)
    _drag(canvas, start, (tri.GetX(), tri.GetY()))
    assert len(_attached_lines(canvas)) == 2
    frame.Destroy()


def test_connection_dots_follow_a_moved_shape(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    canvas.InsertShape(a, 0)
    canvas.select(a)
    dots = [n for n in canvas.nodes if isinstance(n, ConnectionHandleNode)]
    before = {n.side: n._port_position() for n in dots}
    a.move(100, 40)
    after = {n.side: n._port_position() for n in dots}
    assert after["left"] == (before["left"][0] + 100, before["left"][1] + 40)
    assert after["top"] == (before["top"][0] + 100, before["top"][1] + 40)
    frame.Destroy()


def test_connection_drag_survives_zero_length_shapes(wx_app):
    """A degenerate line must not break hit-testing during a connection drag."""
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    b = wxdiagram.ConnectableEllipseShape()
    b.x, b.y = [450, 570], [250, 350]
    zero = wxdiagram.LinesShape([(700, 600), (700, 600)])
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 0)
    canvas.InsertShape(zero, 0)

    start = a.getPort("output", 0)
    _hover(canvas, start)
    _drag(canvas, start, (b.GetX(), b.GetY()))

    lines = _attached_lines(canvas)
    assert len(lines) == 1
    assert lines[0]._from is a
    assert lines[0]._to is b
    assert not any(isinstance(s, wxdiagram.ConnectionShape) for s in canvas.diagram.shapes)
    frame.Destroy()


def test_connection_dot_is_found_just_outside_the_edge(wx_app):
    """Fractional zoom means an integer click can land just outside a shape."""
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    canvas.InsertShape(a, 0)

    node = canvas._connection_dot_at_point((50, 100.4))
    assert isinstance(node, ConnectionHandleNode)
    assert node.item is a
    assert node.side == "left"
    frame.Destroy()


def test_second_connection_from_the_same_shape_works(wx_app):
    from wxdiagram.shapesdemo import DemoTriangle

    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    b = wxdiagram.ConnectableEllipseShape()
    b.x, b.y = [450, 570], [250, 350]
    c = DemoTriangle([(650, 500), (760, 650), (540, 650)])
    for shape in (a, b, c):
        canvas.InsertShape(shape, 0)

    _hover(canvas, a.getPort("output", 0))
    _drag(canvas, a.getPort("output", 0), (b.GetX(), b.GetY()))
    assert len(_attached_lines(canvas)) == 1

    # Select something else, then start a second connection from the same shape.
    canvas.deselect()
    canvas.select(b)
    _hover(canvas, a.getPort("output", 1))
    _drag(canvas, a.getPort("output", 1), (c.GetX(), c.GetY()))
    assert len(_attached_lines(canvas)) == 2
    assert not any(isinstance(s, wxdiagram.ConnectionShape) for s in canvas.diagram.shapes)
    frame.Destroy()


def test_connection_started_from_a_top_dot_uses_that_dot(wx_app):
    from wxdiagram.core import ConnectionShape

    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    canvas.InsertShape(a, 0)
    top = a.connection_points()["top"]
    node = canvas._connection_dot_at_point(top)
    assert node is not None and node.side == "top"

    node.move(30, 20)
    conn = next(s for s in canvas.diagram.shapes if isinstance(s, ConnectionShape))
    assert conn.start_point == top
    conn.draw(wx.MemoryDC(wx.Bitmap(10, 10)))
    assert (conn.x[0], conn.y[0]) == top
    frame.Destroy()


def test_legacy_inode_drop_preserves_edge_type(wx_app):
    """Pynsource still uses INode drop ports to choose Shift/Alt edges."""
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    b = wxdiagram.Block()
    b.x, b.y = [450, 550], [250, 350]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 0)

    calls = []
    original = canvas.join_shapes

    def recording(from_shape, to_shape, edge_type="association"):
        calls.append(edge_type)
        return original(from_shape, to_shape, edge_type)

    canvas.join_shapes = recording
    start = a.getPort("output", 0)
    end = b.getPort("input", 0)

    def evt(wx_type, diagram_xy, down=False, shift=False):
        client = canvas.diagram_point_to_client_coords(*diagram_xy)
        e = wx.MouseEvent(wx_type)
        e.SetPosition(wx.Point(int(client[0]), int(client[1])))
        e.SetX(int(client[0]))
        e.SetY(int(client[1]))
        e.SetEventObject(canvas)
        if down:
            e.SetLeftDown(True)
        if shift:
            e.SetShiftDown(True)
        return e

    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_MOTION, start))
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_LEFT_DOWN, start))
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_MOTION, end, down=True))
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_LEFT_UP, end, shift=True))
    wx.Yield()

    assert calls == ["generalisation"]
    assert not any(isinstance(s, wxdiagram.ConnectionShape) for s in canvas.diagram.shapes)
    frame.Destroy()


def test_legacy_drop_ports_are_round_like_selection_dots(wx_app):
    """Source dots and destination drop ports should share one round style."""
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    canvas.InsertShape(a, 0)

    dc = _mock_dc()
    for node in (INode(a, 0, canvas), ONode(a, 0, canvas)):
        node.draw(dc)
        circles = [call for call in dc.calls if call[0] == "DrawCircle"]
        assert circles, f"{type(node).__name__} did not draw a round port"
        assert circles[-1][1][2] == ConnectionHandleNode.RADIUS
    frame.Destroy()


def test_body_drop_preserves_shift_edge_type(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.showDropPorts = False
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    b = wxdiagram.Block()
    b.x, b.y = [450, 550], [250, 350]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 0)

    calls = []
    original = canvas.join_shapes

    def recording(from_shape, to_shape, edge_type="association"):
        calls.append(edge_type)
        return original(from_shape, to_shape, edge_type)

    canvas.join_shapes = recording
    start = a.getPort("output", 0)
    end = (b.GetX(), b.GetY())

    def evt(wx_type, diagram_xy, down=False, shift=False):
        client = canvas.diagram_point_to_client_coords(*diagram_xy)
        e = wx.MouseEvent(wx_type)
        e.SetPosition(wx.Point(int(client[0]), int(client[1])))
        e.SetX(int(client[0]))
        e.SetY(int(client[1]))
        e.SetEventObject(canvas)
        if down:
            e.SetLeftDown(True)
        if shift:
            e.SetShiftDown(True)
        return e

    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_MOTION, start))
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_LEFT_DOWN, start))
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_MOTION, end, down=True))
    canvas.GetEventHandler().ProcessEvent(evt(wx.wxEVT_LEFT_UP, end, shift=True))
    wx.Yield()

    assert calls == ["generalisation"]
    assert not any(isinstance(s, wxdiagram.ConnectionShape) for s in canvas.diagram.shapes)
    frame.Destroy()


def test_connection_drag_released_on_empty_space_removes_the_temp_line(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    canvas.InsertShape(a, 0)

    start = a.getPort("output", 0)
    _hover(canvas, start)
    _drag(canvas, start, (700, 500))

    assert not any(isinstance(s, wxdiagram.ConnectionShape) for s in canvas.diagram.shapes)
    assert not _attached_lines(canvas)
    frame.Destroy()


def test_ports_appear_only_as_drag_targets(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [50, 150], [50, 150]
    canvas.InsertShape(a, 0)

    # A selected connectable shape shows four corner handles and four side
    # connection dots.  The two sets never occupy the same position.
    canvas.select(a)
    handles = [n for n in canvas.nodes if isinstance(n, ResizeableNode)]
    ports = [n for n in canvas.nodes if isinstance(n, ConnectionHandleNode)]
    assert len(handles) == 4
    assert len(ports) == 4
    handle_points = {n._handle_xy() for n in handles}
    port_points = {n._port_position() for n in ports}
    assert handle_points.isdisjoint(port_points)

    # Selected dots stay visible while the pointer moves elsewhere.
    _hover(canvas, (700, 500))
    assert len([n for n in canvas.nodes if isinstance(n, ConnectionHandleNode)]) == 4
    canvas.deselect()

    # Hovering an unselected shape shows its dots ...
    _hover(canvas, (100, 100))
    ports = [n for n in canvas.nodes if isinstance(n, ConnectionHandleNode)]
    assert len(ports) == 4
    assert all(getattr(n, "_is_hover_port", False) for n in ports)

    # ... and moving away clears them again.
    _hover(canvas, (700, 500))
    assert not any(isinstance(n, ConnectionHandleNode) for n in canvas.nodes)
    frame.Destroy()


def test_attached_line_endpoints_do_not_follow_unrelated_clicks(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [0, 100], [0, 100]
    b = wxdiagram.Block()
    b.x, b.y = [400, 500], [300, 400]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 1)
    canvas.join_shapes(a, b)
    line = _attached_lines(canvas)[0]
    dc = wx.MemoryDC(wx.Bitmap(800, 600))
    line.draw(dc)
    before = line.GetEnds()

    # selecting the line and clicking elsewhere must not move the edge
    canvas.select(line)
    line.draw(dc)
    assert line.GetEnds() == before
    canvas.deselect()

    _click(canvas, (700, 500))
    line.draw(dc)
    after = line.GetEnds()
    dc.SelectObject(wx.NullBitmap)
    assert before == after
    frame.Destroy()


def test_demo_composite_is_placed_where_requested(wx_app):
    """A shadowed loop variable once moved the demo's composite to the wrong place."""
    from wxdiagram.demo import make_composite

    comp = make_composite(620, 50)
    assert comp.x[0] == 620
    assert comp.y[0] == 50
    assert len(comp.GetChildren()) == 4


def test_ellipse_draw_accepts_float_coordinates(wx_app):
    """Dragging a shape adds float deltas; wx DCs only accept ints."""
    frame, canvas = _make_canvas(wx_app)
    ellipse = wxdiagram.ConnectableEllipseShape()
    ellipse.x = [100.5, 250.25]
    ellipse.y = [100.5, 200.75]
    canvas.InsertShape(ellipse, 0)
    dc = wx.MemoryDC(wx.Bitmap(800, 600))
    ellipse.draw(dc)
    dc.SelectObject(wx.NullBitmap)
    frame.Destroy()


def test_attached_line_follows_shape_moves(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a = wxdiagram.Block()
    a.x, a.y = [0, 100], [0, 50]
    b = wxdiagram.Block()
    b.x, b.y = [0, 100], [200, 250]
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 1)

    canvas.join_shapes(a, b)
    line = _attached_lines(canvas)[0]
    assert line._from is a
    assert line._to is b
    # straight down: bottom edge of a to top edge of b
    assert line.GetEnds() == pytest.approx((50, 50, 50, 200))

    # drag b to a new position via the real mouse path; the edge re-routes
    _drag(canvas, (50, 225), (60, 245))
    assert line.GetEnds() == pytest.approx((51.1363636, 50, 58.8636364, 220))
    _assert_routed_between(line, a, b)
    frame.Destroy()


def test_attached_lines_route_from_all_directions(wx_app):
    frame, canvas = _make_canvas(wx_app)
    centre = _block(300, 300)
    canvas.InsertShape(centre, 0)

    # target centres at the 8 compass points around the centre block
    targets = [
        (650, 350),
        (560, 560),
        (350, 650),
        (140, 560),
        (50, 350),
        (140, 140),
        (350, 50),
        (560, 140),
    ]
    for tx, ty in targets:
        target = _block(tx - 50, ty - 50)
        canvas.InsertShape(target, 999)
        canvas.join_shapes(centre, target)
        line = next(s for s in _attached_lines(canvas) if s._to is target)
        _assert_routed_between(line, centre, target)
    assert len(_attached_lines(canvas)) == 8
    frame.Destroy()


def test_edge_follows_shape_orbiting_360_degrees(wx_app):
    """The reported regression: orbit a shape around another and the edge
    must always meet both boxes on the facing sides."""
    import math

    frame, canvas = _make_canvas(wx_app)
    a = _block(300, 300)
    b = _block(550, 300)  # east of a, centre (600, 350)
    canvas.InsertShape(a, 0)
    canvas.InsertShape(b, 1)
    canvas.join_shapes(a, b)
    line = _attached_lines(canvas)[0]

    for angle_deg in range(0, 360, 45):
        radians = math.radians(angle_deg)
        want_x = 350 + 250 * math.cos(radians)
        want_y = 350 + 250 * math.sin(radians)
        b.move(want_x - b.GetX(), want_y - b.GetY())
        b.MoveLinks(dc=None)
        _assert_routed_between(line, a, b)
    frame.Destroy()


def test_get_port_numbers(wx_app):
    block = wxdiagram.Block()
    block.x, block.y = [10, 110], [20, 80]
    assert block.getPort("input", 0) == (10, 50)
    assert block.getPort("output", 0) == (110, 50)
    assert block.getPort("input", 1) == (60, 20)
    assert block.getPort("output", 2) == (60, 80)


def test_polygon_draws_a_closed_polygon(wx_app):
    """PolygonShape used to inherit an open-polyline draw, losing one edge."""
    poly = wxdiagram.PolygonShape()
    poly.Create([(0, -40), (60, 0), (0, 40), (-60, 0)])
    dc = _mock_dc()
    poly.draw(dc)
    calls = [call for call in dc.calls if call[0] == "DrawPolygon"]
    assert calls, "PolygonShape did not draw a polygon"
    assert len(calls[0][1][0]) == 4


def test_block_sets_its_own_text_colour_before_drawing(wx_app):
    """A PaintDC's inherited text colour must not decide whether labels show."""
    block = wxdiagram.Block()
    block.label = "Client"
    dc = _mock_dc()
    block.draw(dc)
    names = [name for name, _args, _kwargs in dc.calls]
    assert "SetTextForeground" in names
    assert "DrawText" in names
    # the colour is set after the background rectangle and before the text
    assert names.index("SetTextForeground") < names.index("DrawText")
