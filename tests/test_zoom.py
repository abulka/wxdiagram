"""Tests for the zoom / pan / virtual-size behaviour of ShapeCanvas."""

import wx

import wxdiagram


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(800, 600))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _add_big_content(canvas):
    """Content much larger than the viewport, so scrolling is meaningful."""
    shape = wxdiagram.RectangleShape(0, 0, 2000, 1600)
    canvas.AddShape(shape)
    return shape


def test_screen_to_diagram_round_trip(wx_app):
    frame, canvas = _make_canvas(wx_app)
    for scale in (0.3, 1.0, 2.5, 5.0):
        canvas.scalex = canvas.scaley = scale
        canvas.SetScrollbars(1, 1, 4000, 4000, 120, 45)
        for x, y in [(0, 0), (100, 50), (321, 222)]:
            diag_x, diag_y = canvas.client_pos_in_diagram_coords(x, y)
            sx, sy = canvas.diagram_point_to_client_coords(diag_x, diag_y)
            assert abs(sx - x) < 1e-6, f"scale={scale} point=({x},{y})"
            assert abs(sy - y) < 1e-6, f"scale={scale} point=({x},{y})"


def test_zoom_to_fit_contains_shapes(wx_app):
    frame, canvas = _make_canvas(wx_app)
    r = wxdiagram.RectangleShape(0, 0, 300, 200)
    r.SetX(150)
    r.SetY(100)
    canvas.AddShape(r)
    canvas.ZoomToFit(margin=20)

    bounds_w, bounds_h = canvas._shapes_bounds()
    client_w, client_h = canvas.GetClientSize()
    virtual_w, virtual_h = canvas.GetVirtualSize()

    # zoom-to-fit must scale the content into the viewport
    assert bounds_w * canvas.scalex <= client_w + 1
    assert bounds_h * canvas.scaley <= client_h + 1
    assert virtual_w >= client_w
    assert virtual_h >= client_h
    assert (
        wxdiagram.ShapeCanvas.ZOOM_MIN_SCALE
        <= canvas.scalex
        <= wxdiagram.ShapeCanvas.ZOOM_MAX_SCALE
    )


def test_zoom_anchor_selection_keeps_point_fixed(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    shape = wxdiagram.RectangleShape(1000, 1000, 1200, 1200)
    canvas.AddShape(shape)
    canvas.select(shape)

    canvas.scalex = canvas.scaley = 1.0
    canvas.SetScrollbars(1, 1, 4000, 4000, 200, 150)

    before = canvas.diagram_point_to_client_coords(shape.GetX(), shape.GetY())
    canvas.ZoomIn(step=1.0, anchor="selection")
    after = canvas.diagram_point_to_client_coords(shape.GetX(), shape.GetY())

    assert abs(before[0] - after[0]) <= 2
    assert abs(before[1] - after[1]) <= 2


def test_zoom_anchor_mouse_point_keeps_point_fixed(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.scalex = canvas.scaley = 1.0
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)

    anchor = (300, 200)
    diagram_point = canvas.client_pos_in_diagram_coords(*anchor)
    canvas.ZoomOut(step=0.2, anchor=anchor)
    after = canvas.diagram_point_to_client_coords(*diagram_point)
    assert abs(after[0] - anchor[0]) <= 2, after
    assert abs(after[1] - anchor[1]) <= 2, after


def test_ctrl_wheel_zoom_keeps_mouse_point_fixed(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.scalex = canvas.scaley = 1.0
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)

    position = wx.Point(300, 200)
    diagram_point = canvas.client_pos_in_diagram_coords(position.x, position.y)
    for rotation in (120, -120, 120):
        evt = wx.MouseEvent(wx.wxEVT_MOUSEWHEEL)
        evt.SetPosition(position)
        evt.SetWheelRotation(rotation)
        evt.SetWheelDelta(120)
        evt.SetControlDown(True)
        canvas.OnMouseWheel(evt)
        after = canvas.diagram_point_to_client_coords(*diagram_point)
        assert abs(after[0] - position.x) <= 2, (rotation, after)
        assert abs(after[1] - position.y) <= 2, (rotation, after)


def _wheel_event(position, rotation, horizontal=False):
    evt = wx.MouseEvent(wx.wxEVT_MOUSEWHEEL)
    evt.SetPosition(position)
    evt.SetWheelRotation(rotation)
    evt.SetWheelDelta(120)
    if horizontal:
        evt.SetWheelAxis(wx.MOUSE_WHEEL_HORIZONTAL)
    return evt


def test_wheel_rotation_up_scrolls_view_up(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)

    canvas.OnMouseWheel(_wheel_event(wx.Point(100, 100), 120))
    assert canvas.GetViewStart()[1] < 400


def test_wheel_rotation_right_scrolls_view_right(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)

    canvas.OnMouseWheel(_wheel_event(wx.Point(100, 100), 120, horizontal=True))
    assert canvas.GetViewStart()[0] > 500


def test_wheel_rotation_down_scrolls_view_down(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)

    canvas.OnMouseWheel(_wheel_event(wx.Point(100, 100), -120))
    assert canvas.GetViewStart()[1] > 400


class _FakeMagnifyEvent:
    def __init__(self, x, y, magnification):
        self._position = wx.Point(x, y)
        self._magnification = magnification

    def GetPosition(self):
        return self._position

    def GetMagnification(self):
        return self._magnification


def test_pinch_zoom_in_keeps_point_fixed(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.scalex = canvas.scaley = 1.0
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)

    anchor = (300, 200)
    diagram_point = canvas.client_pos_in_diagram_coords(*anchor)
    canvas.OnMagnify(_FakeMagnifyEvent(anchor[0], anchor[1], 0.1))
    assert canvas.scalex > 1.0
    after = canvas.diagram_point_to_client_coords(*diagram_point)
    assert abs(after[0] - anchor[0]) <= 2, after
    assert abs(after[1] - anchor[1]) <= 2, after


def test_pinch_zoom_out_is_clamped(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.scalex = canvas.scaley = 1.0
    canvas.OnMagnify(_FakeMagnifyEvent(10, 10, -5.0))
    assert canvas.scalex == wxdiagram.ShapeCanvas.ZOOM_MIN_SCALE


def test_zoom_clamped_to_min_max(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.ZoomTo(100.0)
    assert canvas.scalex == wxdiagram.ShapeCanvas.ZOOM_MAX_SCALE
    canvas.ZoomTo(0.0001)
    assert canvas.scalex == wxdiagram.ShapeCanvas.ZOOM_MIN_SCALE


def test_virtual_size_covers_bounds_after_add(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.RectangleShape(0, 0, 400, 300)
    canvas.AddShape(shape)
    bounds_x, bounds_y = canvas._shapes_bounds()
    client_w, client_h = canvas.GetClientSize()
    virtual_w, virtual_h = canvas.GetVirtualSize()
    assert virtual_w >= min(bounds_x * canvas.scalex + canvas.CANVAS_MARGIN, client_w)
    assert virtual_h >= min(bounds_y * canvas.scaley + canvas.CANVAS_MARGIN, client_h)
    assert canvas.scalex == 1.0


def test_scroll_is_clamped_to_content(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    canvas.update_virtual_size()
    # try to scroll far into the void
    canvas.Scroll(99999, 99999)
    sx, sy = canvas.GetViewStart()
    max_sx = max(0, canvas.GetVirtualSize()[0] - canvas.GetClientSize()[0])
    max_sy = max(0, canvas.GetVirtualSize()[1] - canvas.GetClientSize()[1])
    assert sx <= max_sx + 1
    assert sy <= max_sy + 1


def test_zoom_out_never_loses_content(wx_app):
    frame, canvas = _make_canvas(wx_app)
    _add_big_content(canvas)
    # zoom all the way out while trying to scroll into the void each time
    for _ in range(40):
        canvas.ZoomOut(step=0.25, anchor=(300, 200))
        canvas.Scroll(99999, 99999)
    x, y = canvas.diagram_point_to_client_coords(0, 0)
    client_w, client_h = canvas.GetClientSize()
    # the content origin must still be reachable on screen
    assert 0 <= x < client_w
    assert 0 <= y < client_h


def test_auto_virtual_size_can_be_disabled(wx_app):
    """Applications that manage their own scrollbars (pynsource) opt out."""
    frame, canvas = _make_canvas(wx_app)
    canvas.autoVirtualSize = False
    before = canvas.GetVirtualSize()
    canvas.AddShape(wxdiagram.RectangleShape(0, 0, 5000, 4000))
    assert canvas.GetVirtualSize() == before


def test_zoom_input_can_be_disabled(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.zoomInputEnabled = False
    _add_big_content(canvas)
    scale = canvas.scalex

    evt = _wheel_event(wx.Point(300, 200), 120)
    evt.SetControlDown(True)
    canvas.OnMouseWheel(evt)

    assert canvas.scalex == scale


def test_subclass_can_handle_shift_wheel_and_delegate_the_rest(wx_app):
    """The pattern pynsource uses for Shift+wheel layout expand/contract."""

    class ShiftAwareCanvas(wxdiagram.ShapeCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.shift_wheel = 0

        def OnMouseWheel(self, event):
            if event.ShiftDown():
                self.shift_wheel += 1
                return
            super().OnMouseWheel(event)

    frame = wx.Frame(None, size=(800, 600))
    canvas = ShiftAwareCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    _add_big_content(canvas)

    shift_evt = _wheel_event(wx.Point(300, 200), 120)
    shift_evt.SetShiftDown(True)
    canvas.OnMouseWheel(shift_evt)
    assert canvas.shift_wheel == 1

    scale = canvas.scalex
    ctrl_evt = _wheel_event(wx.Point(300, 200), 120)
    ctrl_evt.SetControlDown(True)
    canvas.OnMouseWheel(ctrl_evt)
    assert canvas.scalex > scale


def test_drag_empty_canvas_pans(wx_app):
    """Dragging empty canvas pans (panOnDrag defaults on)."""
    frame, canvas = _make_canvas(wx_app)
    canvas.AddShape(wxdiagram.RectangleShape(0, 0, 200, 200))
    canvas.SetScrollbars(1, 1, 4000, 4000, 500, 400)
    wx.Yield()

    def evt(wx_type, position, down=False):
        e = wx.MouseEvent(wx_type)
        e.SetPosition(wx.Point(*position))
        e.SetX(position[0])
        e.SetY(position[1])
        e.SetEventObject(canvas)
        if down:
            e.SetLeftDown(True)
        return e

    before = canvas.GetViewStart()
    canvas.OnLeftDown(evt(wx.wxEVT_LEFT_DOWN, (600, 500), down=True))
    canvas.OnMotion(evt(wx.wxEVT_MOTION, (560, 470), down=True))
    canvas.OnLeftUp(evt(wx.wxEVT_LEFT_UP, (560, 470)))
    after = canvas.GetViewStart()

    assert after != before
    frame.Destroy()
