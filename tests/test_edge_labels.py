"""Edge (line) labels: placement, drawing and hit-testing."""

import wx

import pytest

import wxdiagram


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(600, 400))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _render(canvas, width=600, height=400):
    bitmap = wx.Bitmap(width, height)
    dc = wx.MemoryDC(bitmap)
    dc.SetBackground(wx.Brush("WHITE"))
    dc.Clear()
    canvas.Redraw(dc)
    dc.SelectObject(wx.NullBitmap)
    return bitmap.ConvertToImage()


def _has_dark_pixels(image, left, top, right, bottom):
    for y in range(top, bottom):
        for x in range(left, right):
            if image.GetRed(x, y) < 100 and image.GetGreen(x, y) < 100:
                return True
    return False


def _event(canvas, wx_type, diagram_xy, down=False):
    client = canvas.diagram_point_to_client_coords(*diagram_xy)
    e = wx.MouseEvent(wx_type)
    e.SetPosition(wx.Point(int(client[0]), int(client[1])))
    e.SetX(int(client[0]))
    e.SetY(int(client[1]))
    e.SetEventObject(canvas)
    if down:
        e.SetLeftDown(True)
    return e


def _line(canvas, start=(50, 200), end=(450, 200)):
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(*start, *end)
    canvas.AddShape(line)
    return line


def test_label_is_drawn_at_the_middle(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = _line(canvas)
    line.AddText("hello")

    image = _render(canvas)

    assert line.GetLabelPosition(0) == (250, 200)
    assert _has_dark_pixels(image, 225, 185, 275, 215)
    # empty space well above the line stays white
    assert not _has_dark_pixels(image, 225, 120, 275, 150)
    frame.Destroy()


def test_label_lines_are_formatted_for_persistence(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = _line(canvas)
    line.SetLabelText(0, "first\nsecond")

    assert len(line._regions[0].GetFormattedText()) == 2
    image = _render(canvas)
    # two rows of text around the middle
    assert _has_dark_pixels(image, 225, 180, 275, 200)
    assert _has_dark_pixels(image, 225, 200, 275, 220)
    frame.Destroy()


def test_label_positions_start_middle_end(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = _line(canvas)

    assert line.GetLabelPosition(1) == (110, 200)  # 15% along a 400px line
    assert line.GetLabelPosition(0) == (250, 200)
    assert line.GetLabelPosition(2) == (390, 200)  # 85%
    frame.Destroy()


def test_label_offset_moves_the_anchor_and_the_hit_area(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = _line(canvas)
    line.SetLabelText(0, "label")
    line.SetLabelPosition(0, 0, -30)

    assert line.GetLabelPosition(0) == (250, 170)

    _render(canvas)  # populates the label rectangles
    assert line.HitTest(250, 170)  # on the label
    assert not line.HitTest(250, 155)  # 15px above the label
    frame.Destroy()


def test_clicking_a_label_selects_the_line(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = _line(canvas)
    line.SetLabelText(0, "label")
    line.SetLabelPosition(0, 0, -30)
    _render(canvas)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (250, 170), down=True))
    assert line in canvas.getSelectedShapes()
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (250, 170)))
    frame.Destroy()


def test_dashed_edge_does_not_leak_its_pen_into_the_next_line(wx_app):
    """Labels set a transparent pen; the next unpenned line must still draw."""
    frame, canvas = _make_canvas(wx_app)
    _line(canvas, start=(20, 200), end=(380, 200))
    dashed = wxdiagram.LineShape()
    dashed.MakeLineControlPoints(2)
    dashed.SetEnds(20, 120, 380, 120)
    dashed.SetPen(wx.Pen(wx.BLACK, 1, wx.PENSTYLE_LONG_DASH))
    dashed.AddText("dashed")
    canvas.AddShape(dashed)  # drawn after `later` in Redraw order

    image = _render(canvas)

    assert _has_dark_pixels(image, 180, 198, 220, 203)  # undecorated line visible
    assert _has_dark_pixels(image, 180, 118, 220, 123)  # dashed line visible
    frame.Destroy()


def test_spline_arrow_references_follow_the_curve(wx_app):
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(3)
    line._lineControlPoints[0] = wx.RealPoint(0, 0)
    line._lineControlPoints[1] = wx.RealPoint(100, 80)
    line._lineControlPoints[2] = wx.RealPoint(200, 0)
    line.SetSpline(True)

    start_ref, end_ref = line._arrow_reference_points()

    # On the curve near the ends, not the far-off middle control point.
    assert start_ref[0] < 30
    assert end_ref[0] > 170
    assert start_ref != (100, 80)
    assert end_ref != (100, 80)


def test_straight_arrow_references_use_the_neighbouring_points(wx_app):
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(0, 0, 100, 0)

    start_ref, end_ref = line._arrow_reference_points()

    assert tuple(start_ref) == (100.0, 0.0)
    assert tuple(end_ref) == (0.0, 0.0)


def test_line_control_point_accessors(wx_app):
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(0, 0, 100, 0)

    line.SetControlPoint(1, 60, 40)

    assert line.GetControlPoints() == [(0.0, 0.0), (60.0, 40.0)]
    assert line.GetEnds() == (0.0, 0.0, 60.0, 40.0)
    with pytest.raises(IndexError):
        line.SetControlPoint(5, 0, 0)


def test_no_label_no_hit_outside_the_line(wx_app):
    frame, canvas = _make_canvas(wx_app)
    line = _line(canvas)
    _render(canvas)

    assert line.HitTest(250, 200)  # on the line
    assert not line.HitTest(250, 170)  # 30px away
    frame.Destroy()
