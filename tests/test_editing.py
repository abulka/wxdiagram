"""Tests for marquee selection, nudging, duplicate and z-order."""

import wx

import wxdiagram


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(900, 700))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _event(canvas, wx_type, diagram_xy, down=False, shift=False, control=False):
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
    return e


def _add_rect(canvas, left, top, right, bottom):
    shape = wxdiagram.RectangleShape(left, top, right, bottom)
    canvas.AddShape(shape)
    return shape


def _marquee(canvas, start, end, shift=False, control=False):
    canvas.OnLeftDown(
        _event(canvas, wx.wxEVT_LEFT_DOWN, start, down=True, shift=shift, control=control)
    )
    canvas.OnMotion(
        _event(canvas, wx.wxEVT_MOTION, end, down=True, shift=shift, control=control)
    )
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
