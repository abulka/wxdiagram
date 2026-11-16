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

    diagram.ShowAll(True)
    assert shape.IsShown()
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
