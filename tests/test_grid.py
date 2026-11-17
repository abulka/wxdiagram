"""Grid, snapping and alignment-guide behaviour."""

import wx

import pytest

import wxdiagram


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(800, 600))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


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


class _CountingDC:
    """Minimal dc that counts the lines drawn."""

    def __init__(self):
        self.lines = 0

    def SetPen(self, *args):
        pass

    def DrawLine(self, *args):
        self.lines += 1


def test_diagram_grid_api():
    diagram = wxdiagram.Diagram()
    assert diagram.GetGridSpacing() == 10
    assert not diagram.GetSnapToGrid()

    diagram.SetGridSpacing(25)
    assert diagram.GetGridSpacing() == 25
    diagram.SetSnapToGrid(True)
    assert diagram.GetSnapToGrid()

    assert diagram.Snap(37, 12) == (25, 0)


def test_canvas_snap_respects_the_flags(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.diagram.SetGridSpacing(10)

    assert canvas.Snap(17, 23) == (17, 23)  # snapping off

    canvas.snapToGrid = True
    assert canvas.Snap(17, 23) == (20, 20)

    canvas.snapToGrid = False
    canvas.diagram.SetSnapToGrid(True)
    assert canvas.Snap(17, 23) == (20, 20)
    frame.Destroy()


def test_snapping_moves_shape_to_grid(wx_app):
    frame, canvas = _make_canvas(wx_app)
    shape = wxdiagram.RectangleShape(100, 100, 300, 200)
    canvas.AddShape(shape)
    canvas.diagram.SetGridSpacing(10)
    canvas.snapToGrid = True

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (200, 150), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (208, 157), down=True))

    assert shape.x == [110, 310]
    assert shape.y == [110, 210]
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (208, 157)))
    frame.Destroy()


def test_alignment_guides_snap_edges(wx_app):
    frame, canvas = _make_canvas(wx_app)
    anchor = wxdiagram.RectangleShape(100, 100, 200, 180)
    moving = wxdiagram.RectangleShape(300, 100, 400, 180)
    canvas.AddShape(anchor)
    canvas.AddShape(moving)

    # Land the moving box's left edge 2 units right of the anchor's right edge;
    # the guide pulls it onto the alignment.
    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (350, 140), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (248, 140), down=True))

    assert moving.x[0] == 200
    assert ("v", 200) in canvas._guides
    canvas.OnLeftUp(_event(canvas, wx.wxEVT_LEFT_UP, (248, 140)))
    assert canvas._guides == []
    frame.Destroy()


def test_alignment_guides_can_be_disabled(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.alignmentGuides = False
    anchor = wxdiagram.RectangleShape(100, 100, 200, 180)
    moving = wxdiagram.RectangleShape(300, 100, 400, 180)
    canvas.AddShape(anchor)
    canvas.AddShape(moving)

    canvas.OnLeftDown(_event(canvas, wx.wxEVT_LEFT_DOWN, (350, 140), down=True))
    canvas.OnMotion(_event(canvas, wx.wxEVT_MOTION, (248, 140), down=True))

    assert moving.x[0] == pytest.approx(198)
    assert canvas._guides == []
    frame.Destroy()


def test_grid_draws_lines_only_when_enabled(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas.diagram.SetGridSpacing(20)

    dc = _CountingDC()
    canvas._draw_grid(dc)
    assert dc.lines == 0  # showGrid defaults off

    canvas.showGrid = True
    dc = _CountingDC()
    canvas._draw_grid(dc)
    assert dc.lines > 0
    frame.Destroy()


def test_guide_lines_are_drawn(wx_app):
    frame, canvas = _make_canvas(wx_app)
    canvas._guides = [("v", 100), ("h", 50)]

    dc = _CountingDC()
    canvas._draw_guides(dc)
    assert dc.lines == 2
    frame.Destroy()
