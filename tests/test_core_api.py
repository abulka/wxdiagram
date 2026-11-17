"""Regression tests for the public canvas/diagram contract."""

import wx

import wxdiagram


def _canvas(wx_app):
    frame = wx.Frame(None)
    canvas = wxdiagram.ShapeCanvas(frame)
    diagram = wxdiagram.Diagram()
    canvas.SetDiagram(diagram)
    return frame, canvas, diagram


def test_set_diagram_connects_canvas_and_shapes(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    assert diagram.GetCanvas() is canvas

    shape = wxdiagram.RectangleShape(0, 0, 100, 50)
    canvas.AddShape(shape)
    assert shape.GetCanvas() is canvas

    frame.Destroy()


def test_add_shape_after_inserts_after_not_before(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    a = wxdiagram.RectangleShape(0, 0, 10, 10)
    b = wxdiagram.RectangleShape(0, 0, 10, 10)
    c = wxdiagram.RectangleShape(0, 0, 10, 10)
    diagram.AddShape(a)
    diagram.AddShape(c)
    diagram.AddShape(b, addAfter=a)
    assert diagram.shapes.index(b) == diagram.shapes.index(a) + 1
    frame.Destroy()


def test_diagram_clear_clears_dc_but_keeps_shapes(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    shape = wxdiagram.RectangleShape(0, 0, 10, 10)
    canvas.AddShape(shape)

    bitmap = wx.Bitmap(20, 20)
    dc = wx.MemoryDC(bitmap)
    diagram.Clear(dc)
    dc.SelectObject(wx.NullBitmap)

    assert diagram.shapes == [shape]
    frame.Destroy()


def test_show_all_toggles_visibility(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    shape = wxdiagram.RectangleShape(0, 0, 10, 10)
    canvas.AddShape(shape)
    assert shape.IsShown()

    diagram.ShowAll(False)
    assert not shape.IsShown()


def test_move_to_uses_top_left_coordinates(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    shape = wxdiagram.RectangleShape(10, 20, 110, 120)
    canvas.AddShape(shape)

    bitmap = wx.Bitmap(10, 10)
    dc = wx.MemoryDC(bitmap)
    shape.MoveTo(dc, 200, 300)
    dc.SelectObject(wx.NullBitmap)

    assert shape.x[0] == 200
    assert shape.y[0] == 300
    assert shape._xpos == 250
    assert shape._ypos == 350
    frame.Destroy()


def test_move_to_refreshes_attached_lines(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    a = wxdiagram.RectangleShape(0, 0, 100, 100)
    b = wxdiagram.RectangleShape(300, 0, 400, 100)
    canvas.AddShape(a)
    canvas.AddShape(b)

    line = wxdiagram.LineShape()
    line.SetCanvas(canvas)
    line.MakeLineControlPoints(2)
    a.AddLine(line, b)
    diagram.AddShape(line)

    before = [wx.RealPoint(p[0], p[1]) for p in line._lineControlPoints]

    bitmap = wx.Bitmap(10, 10)
    dc = wx.MemoryDC(bitmap)
    b.MoveTo(dc, 800, 400)
    dc.SelectObject(wx.NullBitmap)

    after = line._lineControlPoints
    assert (before[0].x, before[0].y) != (after[0].x, after[0].y) or (
        before[-1].x,
        before[-1].y,
    ) != (after[-1].x, after[-1].y)
    frame.Destroy()


def test_get_content_bounds_is_overridable(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    canvas.AddShape(wxdiagram.RectangleShape(0, 0, 500, 400))

    assert canvas.getContentBounds() == canvas._shapes_bounds()

    class CroppedCanvas(wxdiagram.ShapeCanvas):
        def getContentBounds(self):
            return 100, 50

    cropped = CroppedCanvas(frame)
    cropped.SetDiagram(wxdiagram.Diagram())
    cropped.AddShape(wxdiagram.RectangleShape(0, 0, 5000, 5000))
    cropped.ZoomToFit(margin=20)

    assert cropped._shapes_bounds() == (100, 50)
    assert cropped.scalex >= wxdiagram.ShapeCanvas.ZOOM_MIN_SCALE
    frame.Destroy()


def test_shape_ids_are_stable_and_findable(wx_app):
    frame, canvas, diagram = _canvas(wx_app)
    a = wxdiagram.RectangleShape(0, 0, 10, 10)
    b = wxdiagram.RectangleShape(0, 0, 10, 10)
    canvas.AddShape(a)
    canvas.AddShape(b)

    assert a.GetId() > 0
    assert b.GetId() > 0
    assert a.GetId() != b.GetId()
    assert diagram.FindShape(a.GetId()) is a
    assert diagram.FindShape(b.GetId()) is b
    assert diagram.FindShape(999999) is None
    frame.Destroy()


def test_line_spline_and_arrow_accessors(wx_app):
    line = wxdiagram.LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(0, 0, 100, 0)

    assert not line.IsSpline()
    line.SetSpline(True)
    assert line.IsSpline()

    arrow = line.AddArrow(wxdiagram.ARROW_ARROW)
    assert line.GetArrows() == [arrow]
    assert line.FindArrowHead(-1, "") is arrow
    assert line.FindArrowHeadId(arrow.GetId()) is arrow
    assert line.DeleteArrowHeadId(arrow.GetId())
    assert line.GetArrows() == []


def test_composite_constraints_can_be_inspected_and_cleaned(wx_app):
    parent = wxdiagram.CompositeShape()
    a = wxdiagram.RectangleShape(0, 0, 10, 10)
    b = wxdiagram.RectangleShape(0, 0, 10, 10)
    parent.AddChild(a)
    parent.AddChild(b)

    constraint = parent.AddSimpleConstraint(wxdiagram.CONSTRAINT_ALIGNED_TOP, a, b)
    assert parent.GetConstraints() == [constraint]

    parent.RemoveChildFromConstraints(b)
    assert parent.GetConstraints() == []


def test_persistence_preserves_shape_ids(wx_app, tmp_path):
    frame, canvas, diagram = _canvas(wx_app)
    shape = wxdiagram.RectangleShape(0, 0, 100, 50)
    canvas.AddShape(shape)
    shape_id = shape.GetId()

    path = tmp_path / "ids.json"
    diagram.Save(path)
    loaded = wxdiagram.Diagram.Load(path)

    assert loaded.shapes[0].GetId() == shape_id
    assert loaded.FindShape(shape_id) is loaded.shapes[0]
    frame.Destroy()
