"""Shape drawing: each shape must set its own pen/brush on the shared dc."""

import wx

import wxdiagram


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(400, 300))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _render(canvas, width=400, height=300):
    bitmap = wx.Bitmap(width, height)
    dc = wx.MemoryDC(bitmap)
    dc.SetBackground(wx.Brush("WHITE"))
    dc.Clear()
    canvas.Redraw(dc)
    dc.SelectObject(wx.NullBitmap)
    return bitmap.ConvertToImage()


def _pixel(image, x, y):
    return image.GetRed(x, y), image.GetGreen(x, y), image.GetBlue(x, y)


def test_ellipse_uses_its_own_brush(wx_app):
    """A shape drawn just before the ellipse must not tint it."""
    frame, canvas = _make_canvas(wx_app)
    red = wxdiagram.RectangleShape(0, 0, 40, 40)
    red.SetBrush(wx.Brush("RED"))

    ellipse = wxdiagram.ConnectableEllipseShape()
    ellipse.x = [100, 300]
    ellipse.y = [100, 250]
    ellipse.SetBrush(wx.Brush("PALE GREEN"))

    # AddShape inserts at the front, so the red box is drawn before the ellipse.
    canvas.AddShape(ellipse)
    canvas.AddShape(red)

    image = _render(canvas)
    r, g, b = _pixel(image, 200, 175)

    assert not (r > 200 and g < 80), "ellipse inherited the red brush"
    assert g > r, f"ellipse should be pale green, got {(r, g, b)}"
    frame.Destroy()


def test_ellipse_is_not_affected_by_a_preceding_dashed_line(wx_app):
    """Labels/dashed lines leave unusual pen/brush state on the dc."""
    frame, canvas = _make_canvas(wx_app)
    dashed = wxdiagram.LineShape()
    dashed.MakeLineControlPoints(2)
    dashed.SetEnds(0, 20, 380, 20)
    dashed.SetPen(wx.Pen(wx.BLACK, 1, wx.PENSTYLE_LONG_DASH))
    dashed.AddText("dashed")

    ellipse = wxdiagram.ConnectableEllipseShape()
    ellipse.x = [100, 300]
    ellipse.y = [100, 250]
    ellipse.SetBrush(wx.Brush("PALE GREEN"))

    canvas.AddShape(ellipse)
    canvas.AddShape(dashed)

    image = _render(canvas)
    r, g, b = _pixel(image, 200, 175)

    assert not (r > 200 and g < 80)
    assert g > r
    frame.Destroy()
