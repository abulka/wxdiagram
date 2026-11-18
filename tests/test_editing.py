"""Tests for marquee selection, nudging, duplicate and z-order."""

import wx

import pytest

import wxdiagram
from wxdiagram.core import ResizeableNode


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(900, 700))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _event(canvas, wx_type, diagram_xy, down=False, shift=False, control=False, alt=False):
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
    if control:
        e.SetControlDown(True)
    if alt:
        e.SetAltDown(True)
    return e


def _add_rect(canvas, left, top, right, bottom):
    shape = wxdiagram.RectangleShape(left, top, right, bottom)
    canvas.AddShape(shape)
    return shape


def _marquee(canvas, start, end, shift=False, control=False):
    canvas.OnLeftDown(
        _event(canvas, wx.wxEVT_LEFT_DOWN, start, down=True, shift=shift, control=control)
    )
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, end, down=True, shift=shift, control=control))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, end, shift=shift, control=control))


def test_marquee_selects_touched_shapes(wx_app):
    frame, canvas = _make_canvas(wx_app)
    near = _add_rect(canvas, 0, 0, 100, 100)
    far = _add_rect(canvas, 300, 300, 400, 400)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    _marquee(canvas, (200, 200), (450, 450))

    assert canvas.getSelectedShapes() == [far]
    assert near not in canvas.getSelectedShapes()
    frame.Destroy()


def test_shift_marquee_adds_to_selection(wx_app):
    frame, canvas = _make_canvas(wx_app)
    near = _add_rect(canvas, 0, 0, 100, 100)
    far = _add_rect(canvas, 300, 300, 400, 400)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    canvas.select(near)
    _marquee(canvas, (200, 200), (450, 450), shift=True)

    assert set(canvas.getSelectedShapes()) == {near, far}
    frame.Destroy()


def test_clicking_empty_canvas_clears_selection(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = _add_rect(canvas, 0, 0, 100, 100)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (500, 500), down=True))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (500, 500)))

    assert canvas.getSelectedShapes() == []
    frame.Destroy()


def test_nudge_selected_moves_shapes(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = _add_rect(canvas, 10, 10, 110, 110)
    canvas.select(shape)

    canvas.nudge_selected(5, -3)

    assert shape.x[0] == 15
    assert shape.y[0] == 7
    frame.Destroy()


def test_duplicate_selected_offsets_and_selects_copy(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = _add_rect(canvas, 10, 10, 110, 110)
    canvas.select(shape)

    clones = canvas.duplicate_selected(offset=(20, 30))

    assert len(clones) == 1
    clone = clones[0]
    assert clone is not shape
    assert (clone.x[0], clone.y[0]) == (30, 40)
    assert canvas.getSelectedShapes() == [clone]
    assert canvas.GetDiagram().GetCount() == 2
    frame.Destroy()


def test_z_order_helpers(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = _add_rect(canvas, 0, 0, 100, 100)
    second = _add_rect(canvas, 20, 20, 120, 120)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    canvas.send_to_back([first])
    assert canvas.GetDiagram().shapes[0] is first

    canvas.bring_to_front([first])
    assert canvas.GetDiagram().shapes[-1] is first
    assert canvas.GetDiagram().shapes[0] is second
    frame.Destroy()


def test_undo_redo_nudge(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = _add_rect(canvas, 10, 10, 110, 110)
    canvas.select(shape)
    start = (shape.x[0], shape.y[0])

    canvas.nudge_selected(5, 7)
    assert (shape.x[0], shape.y[0]) == (start[0] + 5, start[1] + 7)
    assert canvas.canUndo()

    canvas.undo()
    assert (shape.x[0], shape.y[0]) == start
    assert canvas.canRedo()

    canvas.redo()
    assert (shape.x[0], shape.y[0]) == (start[0] + 5, start[1] + 7)
    frame.Destroy()


def test_undo_duplicate(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = _add_rect(canvas, 10, 10, 110, 110)
    canvas.select(shape)

    canvas.duplicate_selected(offset=(20, 20))
    assert canvas.GetDiagram().GetCount() == 2

    canvas.undo()
    assert canvas.GetDiagram().GetCount() == 1
    frame.Destroy()


def test_undo_z_order(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = _add_rect(canvas, 0, 0, 100, 100)
    _add_rect(canvas, 20, 20, 120, 120)
    original = list(canvas.GetDiagram().shapes)

    canvas.send_to_back([first])
    assert canvas.GetDiagram().shapes != original
    canvas.undo()
    assert canvas.GetDiagram().shapes == original
    frame.Destroy()


def test_undo_mouse_move(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = _add_rect(canvas, 100, 100, 200, 200)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()
    start = (shape.x[0], shape.y[0])

    centre = (shape.GetX(), shape.GetY())
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, centre, down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (centre[0] + 20, centre[1] + 10), down=True))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (centre[0] + 20, centre[1] + 10)))

    assert (shape.x[0], shape.y[0]) != start
    canvas.undo()
    assert (shape.x[0], shape.y[0]) == start
    frame.Destroy()


def test_dragging_one_of_multiple_selected_moves_all(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = _add_rect(canvas, 100, 100, 200, 200)
    second = _add_rect(canvas, 300, 300, 400, 400)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    canvas.select(first)
    canvas.select(second)
    start_first = (first.x[0], first.y[0])
    start_second = (second.x[0], second.y[0])

    centre = (first.GetX(), first.GetY())
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, centre, down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (centre[0] + 20, centre[1] + 10), down=True))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (centre[0] + 20, centre[1] + 10)))

    assert (first.x[0] - start_first[0], first.y[0] - start_first[1]) == (20, 10)
    assert (second.x[0] - start_second[0], second.y[0] - start_second[1]) == (20, 10)
    assert set(canvas.getSelectedShapes()) == {first, second}
    frame.Destroy()


def test_group_drag_does_not_move_an_attached_edge_twice(wx_app):
    """An attached edge follows its shapes; moving it too overshoots by delta."""
    frame, canvas = _make_canvas(wx_app)
    first = _add_rect(canvas, 100, 100, 250, 200)
    second = _add_rect(canvas, 450, 100, 600, 200)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()
    line = canvas.join_shapes(first, second)
    line.SetRouteMode("straight")

    # pynsource appends edges after the boxes, so the edge is moved after the
    # shapes in the selection loop.  That is the order that exposed the bug.
    canvas.diagram.ChangeShapeOrder(line, len(canvas.diagram.shapes) - 1)
    canvas.select(first)
    canvas.select(second)
    canvas.select(line)
    assert canvas.getSelectedShapes()[-1] is line

    centre = (first.GetX(), first.GetY())
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, centre, down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (centre[0] + 40, centre[1] + 20), down=True))
    assert (first.x[0], first.y[0]) == (140, 120)
    assert (second.x[0], second.y[0]) == (490, 120)
    assert tuple(line.GetEnds()) == tuple(line.FindLineEndPoints())
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (centre[0] + 40, centre[1] + 20)))
    frame.Destroy()


def test_dragging_an_attached_edge_alone_does_not_stretch_it(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = _add_rect(canvas, 100, 100, 250, 200)
    second = _add_rect(canvas, 450, 100, 600, 200)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()
    line = canvas.join_shapes(first, second)
    line.SetRouteMode("straight")
    before_ends = tuple(line.GetEnds())
    before_shapes = [(first.x[0], first.y[0]), (second.x[0], second.y[0])]

    canvas.select(line)
    midpoint = (350, 150)
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, midpoint, down=True))
    canvas.OnMotion(
        _event(canvas, wx.wxEVT_MOTION, (midpoint[0] + 80, midpoint[1] + 40), down=True)
    )
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (midpoint[0] + 80, midpoint[1] + 40)))

    assert tuple(line.GetEnds()) == before_ends
    assert [(first.x[0], first.y[0]), (second.x[0], second.y[0])] == before_shapes
    frame.Destroy()


def test_set_diagram_clears_old_selection_chrome(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.Block()
    shape.x = [100, 200]
    shape.y = [100, 200]
    canvas.AddShape(shape)
    canvas.select(shape)
    assert canvas.getSelectedShapes() == [shape]
    assert canvas.nodes, "selection handles were not created"

    canvas.SetDiagram(wxdiagram.Diagram())

    assert canvas.getSelectedShapes() == []
    assert canvas.nodes == []
    assert canvas._hover_shape is None
    assert not shape.Selected()
    frame.Destroy()


def test_delete_all_shapes_clears_selection_chrome(wx_app):
    """Pynsource's sample loader reuses the diagram and calls DeleteAllShapes."""
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.Block()
    shape.x = [100, 200]
    shape.y = [100, 200]
    canvas.AddShape(shape)
    canvas.select(shape)
    assert canvas.nodes

    canvas.GetDiagram().DeleteAllShapes()

    assert canvas.GetDiagram().GetCount() == 0
    assert canvas.getSelectedShapes() == []
    assert canvas.nodes == []
    assert canvas._hover_shape is None
    frame.Destroy()


def test_deleting_one_selected_shape_clears_only_its_handles(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = wxdiagram.Block()
    first.x, first.y = [100, 200], [100, 200]
    second = wxdiagram.Block()
    second.x, second.y = [300, 400], [100, 200]
    canvas.AddShape(first)
    canvas.AddShape(second)
    canvas.select(first)
    canvas.select(second)
    assert any(getattr(node, "item", None) is first for node in canvas.nodes)

    canvas.GetDiagram().DeleteShape(first)

    assert first not in canvas.getSelectedShapes()
    assert not any(getattr(node, "item", None) is first for node in canvas.nodes)
    assert second in canvas.getSelectedShapes()
    frame.Destroy()


def test_click_does_not_reorder_when_disabled(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.bringClickedShapeToFront = False
    first = _add_rect(canvas, 0, 0, 100, 100)
    second = _add_rect(canvas, 200, 200, 300, 300)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    order = list(canvas.GetDiagram().shapes)
    centre = (first.GetX(), first.GetY())
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, centre, down=True))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, centre))

    assert canvas.GetDiagram().shapes == order
    assert first in canvas.getSelectedShapes()
    assert second not in canvas.getSelectedShapes()
    frame.Destroy()


def test_bring_forward_send_backward(wx_app):
    frame, canvas = _make_canvas(wx_app)
    first = _add_rect(canvas, 0, 0, 100, 100)
    second = _add_rect(canvas, 20, 20, 120, 120)
    third = _add_rect(canvas, 40, 40, 140, 140)
    original = list(canvas.GetDiagram().shapes)
    assert original == [third, second, first]

    canvas.bring_forward([second])
    assert canvas.GetDiagram().shapes == [third, first, second]
    canvas.send_backward([second])
    assert canvas.GetDiagram().shapes == original
    frame.Destroy()


def test_add_image_scales_centers_and_sends_to_back(wx_app, tmp_path):
    frame, canvas = _make_canvas(wx_app)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    image = wx.Image(40, 30)
    image.SetRGB(wx.Rect(0, 0, 40, 30), 200, 100, 50)
    path = tmp_path / "sample.png"
    image.SaveFile(str(path), wx.BITMAP_TYPE_PNG)

    client_w, client_h = canvas.GetClientSize()
    centre = canvas.client_pos_in_diagram_coords(client_w / 2, client_h / 2)
    shape = canvas.AddImage(str(path), max_size=(20, 20), center=True, send_to_back=True)

    assert shape is not None
    assert shape.GetBitmap().GetWidth() == 20
    assert shape.GetBitmap().GetHeight() == 15
    assert canvas.GetDiagram().shapes[0] is shape
    assert abs(shape.GetX() - centre[0]) <= 1
    assert abs(shape.GetY() - centre[1]) <= 1
    frame.Destroy()


def test_resizable_bitmap_shape(wx_app):
    image = wx.Image(40, 30)
    image.SetRGB(wx.Rect(0, 0, 40, 30), 200, 100, 50)
    shape = wxdiagram.ResizableBitmapShape()
    shape.SetBitmap(wx.Bitmap(image))

    shape.SetSize(20, 15)
    assert shape.GetBoundingBoxMin() == (20, 15)
    assert (shape.x[1] - shape.x[0], shape.y[1] - shape.y[0]) == (20, 15)

    shape.ResetSize()
    assert shape.GetBoundingBoxMin() == (40, 30)


def test_resizable_rectangle_selection_creates_handles(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(0, 0, 120, 80)
    canvas.AddShape(shape)
    canvas.select(shape)
    assert shape in canvas.getSelectedShapes()
    assert canvas.nodes
    frame.Destroy()


def test_bitmap_handle_resizes_bitmap(wx_app):
    image = wx.Image(40, 30)
    image.SetRGB(wx.Rect(0, 0, 40, 30), 200, 100, 50)
    shape = wxdiagram.ResizableBitmapShape()
    shape.SetBitmap(wx.Bitmap(image))
    shape.x = [0, 40]
    shape.y = [0, 30]
    shape.SetSize(40, 30)

    shape.move_handle(1, 20, 10)
    # Proportional by default: 4:3 is kept, driven by the x axis.
    assert shape.GetBoundingBoxMin() == (60, 45)


def test_bitmap_handle_free_aspect_follows_each_axis(wx_app):
    image = wx.Image(40, 30)
    shape = wxdiagram.ResizableBitmapShape()
    shape.SetBitmap(wx.Bitmap(image))
    shape.x = [0, 40]
    shape.y = [0, 30]

    shape.move_handle(1, 20, 10, free_aspect=True)
    assert shape.GetBoundingBoxMin() == (60, 40)


def test_bitmap_resize_tracks_mouse_at_fractional_zoom(wx_app):
    """Resizing must not snap geometry to whole units.

    At a non-integer zoom (the demo starts zoomed to fit) the diagram-space
    drag delta is fractional.  Truncating the size on every motion event threw
    that fraction away, so the image fell further and further behind the
    cursor - and it never caught up.
    """
    frame, canvas = _make_canvas(wx_app)
    zoom = 1.0523
    canvas.scalex = canvas.scaley = zoom

    shape = wxdiagram.ResizableBitmapShape()
    # Square image: the default proportional resize then matches the equal
    # x/y mouse steps, so the handle must track the mouse exactly.
    shape.SetBitmap(wx.Bitmap(wx.Image(200, 200)))
    shape.move_to(100, 100)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)
    start_w, start_h = shape.GetBoundingBoxMin()

    mouse_x, mouse_y = canvas.diagram_point_to_client_coords(shape.x[1], shape.y[1])
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (shape.x[1], shape.y[1]), down=True))
    assert isinstance(canvas.getSelectedShapes()[0], ResizeableNode)

    # Small 2px steps: at this zoom each one is less than one diagram unit.
    for _ in range(20):
        mouse_x += 2
        mouse_y += 2
        point = canvas.client_pos_in_diagram_coords(mouse_x, mouse_y)
        canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, point, down=True))

    handle_x, handle_y = canvas.diagram_point_to_client_coords(shape.x[1], shape.y[1])
    assert handle_x == pytest.approx(mouse_x, abs=1.0)
    assert handle_y == pytest.approx(mouse_y, abs=1.0)

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(start_w + 40 / zoom, abs=0.01)
    assert height == pytest.approx(start_h + 40 / zoom, abs=0.01)
    frame.Destroy()


def test_bitmap_handle_clamps_at_the_opposite_corner(wx_app):
    shape = wxdiagram.ResizableBitmapShape()
    shape.SetBitmap(wx.Bitmap(wx.Image(40, 30)))
    shape.x = [0, 40]
    shape.y = [0, 30]

    # Drag the top-left handle past the bottom-right one.
    shape.move_handle(0, 100, 100)

    assert shape.GetBoundingBoxMin() == (1.0, 1.0)
    assert shape.x == [39.0, 40.0]
    assert shape.y == [29.0, 30.0]
    assert shape.HitTest(39.5, 29.5)  # must not trip RectangleShape.sanity()


def test_resize_is_proportional_by_default(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)  # 200 x 100
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (shape.x[1], shape.y[1]), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (shape.x[1] + 40, shape.y[1] + 5), down=True))

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(240)
    assert height == pytest.approx(120)  # 2:1 kept, driven by the x axis
    frame.Destroy()


def test_shift_resize_allows_free_aspect(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)  # 200 x 100
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (shape.x[1], shape.y[1]), down=True))
    canvas.OnMotion(
        _event(canvas, wx.wxEVT_MOTION, (shape.x[1] + 40, shape.y[1] + 5), down=True, shift=True)
    )

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(240)
    assert height == pytest.approx(105)  # each axis follows the mouse
    frame.Destroy()


def test_bitmap_resize_is_proportional_by_default(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableBitmapShape()
    shape.SetBitmap(wx.Bitmap(wx.Image(200, 100)))
    shape.move_to(100, 100)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (shape.x[1], shape.y[1]), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (shape.x[1] + 40, shape.y[1] + 5), down=True))

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(240)
    assert height == pytest.approx(120)
    frame.Destroy()


def test_rectangle_handle_clamps_instead_of_inverting(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 250)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    node = next(n for n in canvas.nodes if isinstance(n, ResizeableNode) and n.index == 0)
    node.move(500, 500)  # drag the top-left handle past the bottom-right one

    assert shape.GetBoundingBoxMin() == (1.0, 1.0)
    assert shape.x == [299.0, 300.0]
    assert shape.y == [249.0, 250.0]
    # Hit-testing calls RectangleShape.sanity(), which used to raise here.
    assert shape.HitTest(299.5, 249.5)
    assert canvas.shapeFromPoint((299.5, 249.5)) is not None
    frame.Destroy()


def test_rectangle_selection_creates_eight_handles(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    nodes = {n.index: n for n in canvas.nodes if isinstance(n, ResizeableNode)}
    assert sorted(nodes) == list(range(8))
    assert nodes[0]._handle_xy() == (100, 100)  # top-left
    assert nodes[1]._handle_xy() == (300, 200)  # bottom-right
    assert nodes[2]._handle_xy() == (300, 100)  # top-right
    assert nodes[3]._handle_xy() == (100, 200)  # bottom-left
    assert nodes[4]._handle_xy() == (100, 150)  # left
    assert nodes[5]._handle_xy() == (300, 150)  # right
    assert nodes[6]._handle_xy() == (200, 100)  # top
    assert nodes[7]._handle_xy() == (200, 200)  # bottom
    frame.Destroy()


def test_edge_handle_resizes_one_axis(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    right = next(n for n in canvas.nodes if isinstance(n, ResizeableNode) and n.index == 5)
    right.move(20, 30)  # the y delta must be ignored for an edge handle
    assert shape.x == [100, 320]
    assert shape.y == [100, 200]

    bottom = next(n for n in canvas.nodes if isinstance(n, ResizeableNode) and n.index == 7)
    bottom.move(0, 50)
    assert shape.GetBoundingBoxMin() == (220, 150)
    frame.Destroy()


def test_corner_handle_works_from_every_corner(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)  # 2:1
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    top_right = next(n for n in canvas.nodes if isinstance(n, ResizeableNode) and n.index == 2)
    top_right.move(-40, -10)

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(160)
    assert height == pytest.approx(80)  # proportional, driven by x
    # bottom-left corner stays anchored
    assert shape.x[0] == pytest.approx(100)
    assert shape.y[1] == pytest.approx(200)
    frame.Destroy()


def test_bitmap_edge_handle_resizes_one_axis(wx_app):
    shape = wxdiagram.ResizableBitmapShape()
    shape.SetBitmap(wx.Bitmap(wx.Image(40, 30)))
    shape.x = [0, 40]
    shape.y = [0, 30]

    shape.move_handle(5, 20, 15)  # right edge
    assert shape.GetBoundingBoxMin() == (60, 30)
    shape.move_handle(4, -10, 0)  # left edge
    assert shape.GetBoundingBoxMin() == (70, 30)


def test_alt_resize_grows_from_the_centre(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)  # 200 x 100
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (shape.x[1], shape.y[1]), down=True))
    canvas.OnMotion(
        _event(canvas, wx.wxEVT_MOTION, (shape.x[1] + 20, shape.y[1] + 5), down=True, alt=True)
    )

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(240)  # both sides grow by the 20px delta
    assert height == pytest.approx(120)  # proportional
    assert (shape.x[0] + shape.x[1]) / 2 == pytest.approx(200)  # centre fixed
    assert (shape.y[0] + shape.y[1]) / 2 == pytest.approx(150)
    frame.Destroy()


def test_alt_shift_resize_from_centre_frees_aspect(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (shape.x[1], shape.y[1]), down=True))
    canvas.OnMotion(
        _event(
            canvas,
            wx.wxEVT_MOTION,
            (shape.x[1] + 20, shape.y[1] + 5),
            down=True,
            alt=True,
            shift=True,
        )
    )

    width, height = shape.GetBoundingBoxMin()
    assert width == pytest.approx(240)
    assert height == pytest.approx(110)  # each side follows its own axis
    frame.Destroy()


def test_tiny_drag_does_not_move_a_shape(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.RectangleShape(100, 100, 300, 200)
    canvas.AddShape(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (200, 150), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (202, 151), down=True))
    assert shape.x == [100, 300]  # inside the 3px tolerance

    # Crossing the threshold applies the whole delta from the press point.
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (210, 150), down=True))
    assert shape.x == [110, 310]
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (210, 150)))
    frame.Destroy()


def test_tiny_drag_does_not_resize(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(100, 100, 300, 200)
    canvas.InsertShape(shape, 0)
    canvas.select(shape)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (300, 200), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (301, 201), down=True))
    assert shape.GetBoundingBoxMin() == (200, 100)

    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (310, 205), down=True))
    assert shape.GetBoundingBoxMin() == (210, 105)
    frame.Destroy()


def test_composite_resizes_and_scales_children(wx_app):
    comp = wxdiagram.CompositeShape()
    child = wxdiagram.Block()
    child.x = [0, 50]
    child.y = [0, 40]
    comp.AddChild(child)
    comp.x = [0, 100]
    comp.y = [0, 80]

    comp.move_handle(1, 100, 80, free_aspect=True)

    assert comp.GetBoundingBoxMin() == (200, 160)
    assert child.x == [0, 100]  # scaled with the frame
    assert child.y == [0, 80]


def test_composite_selection_creates_resize_handles(wx_app):
    frame, canvas = _make_canvas(wx_app)
    comp = wxdiagram.CompositeShape()
    comp.AddChild(wxdiagram.Block())
    canvas.InsertShape(comp, 0)
    canvas.select(comp)

    handles = [n for n in canvas.nodes if isinstance(n, ResizeableNode)]
    assert len(handles) == 8
    frame.Destroy()


def test_polygon_is_clickable_inside_not_just_on_its_outline(wx_app):
    frame, canvas = _make_canvas(wx_app)
    diamond = wxdiagram.PolygonShape()
    diamond.Create([(0, -50), (50, 0), (0, 50), (-50, 0)])
    diamond.move_to(200, 200)
    canvas.AddShape(diamond)

    centre = ((min(diamond.x) + max(diamond.x)) / 2, (min(diamond.y) + max(diamond.y)) / 2)
    assert diamond.HitTest(*centre)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, centre, down=True))
    assert diamond in canvas.getSelectedShapes()
    frame.Destroy()


def test_selectable_text_can_be_selected_and_moved(wx_app):
    frame, canvas = _make_canvas(wx_app)
    caption = wxdiagram.SelectableTextShape(100, 100, "hello caption")
    canvas.AddShape(caption)
    canvas.SetScrollbars(1, 1, 2000, 2000, 0, 0)
    wx.Yield()

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (110, 105), down=True))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (110, 105)))
    assert caption in canvas.getSelectedShapes()

    centre = (caption.x[0] + 5, caption.y[0] + 5)
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, centre, down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (centre[0] + 20, centre[1] + 10), down=True))
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (centre[0] + 20, centre[1] + 10)))
    assert caption.x[0] == 120
    assert caption.y[0] == 110
    frame.Destroy()
