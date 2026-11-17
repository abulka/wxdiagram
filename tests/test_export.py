"""PNG export and buffered painting."""

import wx

import wxdiagram


def _make_canvas(wx_app, canvas_class=None):
    frame = wx.Frame(None, size=(800, 600))
    canvas = (canvas_class or wxdiagram.ShapeCanvas)(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _export(canvas, path, **kwargs):
    assert canvas.ExportPng(path, **kwargs)
    image = wx.Image(str(path))
    assert image.IsOk()
    return image


def test_export_png_renders_the_diagram(wx_app, tmp_path):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.RectangleShape(10, 20, 60, 70)
    shape.SetBrush(wx.Brush("RED"))
    shape.SetPen(wx.TRANSPARENT_PEN)
    canvas.AddShape(shape)

    image = _export(canvas, tmp_path / "diagram.png", margin=5)

    assert (image.GetWidth(), image.GetHeight()) == (60, 60)  # 50x50 + 2*5
    # (10, 20) is the content origin, so it lands at the margin.
    r, g, b = image.GetRed(30, 30), image.GetGreen(30, 30), image.GetBlue(30, 30)
    assert r > 200 and g < 80 and b < 80


def test_export_png_scales_and_omits_handles(wx_app, tmp_path):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.ResizableRectangleShape(10, 20, 60, 70)
    shape.SetBrush(wx.Brush("RED"))
    shape.SetPen(wx.TRANSPARENT_PEN)
    canvas.AddShape(shape)
    canvas.select(shape)  # handles are on screen, but must not be exported

    image = _export(canvas, tmp_path / "diagram2x.png", scale=2.0)

    assert (image.GetWidth(), image.GetHeight()) == (100, 100)
    r, g, b = image.GetRed(10, 10), image.GetGreen(10, 10), image.GetBlue(10, 10)
    assert r > 200 and g < 80 and b < 80  # top-left corner is shape, not a black handle


def test_export_png_with_empty_diagram(wx_app, tmp_path):
    frame, canvas = _make_canvas(wx_app)
    image = _export(canvas, tmp_path / "empty.png")
    assert (image.GetWidth(), image.GetHeight()) == (1, 1)


def test_buffered_painting_is_off_by_default(wx_app):
    frame, canvas = _make_canvas(wx_app)
    assert canvas.bufferedPainting is False
    frame.Destroy()


def test_buffered_painting_sets_the_paint_background_style(wx_app):
    class BufferedCanvas(wxdiagram.ShapeCanvas):
        bufferedPainting = True

    frame, canvas = _make_canvas(wx_app, BufferedCanvas)
    assert canvas.GetBackgroundStyle() == wx.BG_STYLE_PAINT
    canvas.Refresh()
    canvas.Update()
    frame.Destroy()
