"""Diagram/Canvas ApplyLayout integration + route-mode persistence."""

import wx

import wxdiagram
from wxdiagram import persistence


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(900, 700))
    canvas = wxdiagram.ShapeCanvas(frame)
    canvas.SetDiagram(wxdiagram.Diagram())
    frame.Show()
    frame.Layout()
    wx.Yield()
    return frame, canvas


def _block(left, top, right, bottom):
    block = wxdiagram.Block()
    block.x = [left, right]
    block.y = [top, bottom]
    return block


def _chain(canvas, n=5):
    boxes = [_block(0, 0, 100, 60) for _ in range(n)]
    for i, box in enumerate(boxes):
        box.move_to(10 + i * 5, 10 + i * 5)  # start stacked
        canvas.AddShape(box)
    for a, b in zip(boxes, boxes[1:]):
        line = canvas.join_shapes(a, b)
        line.SetRouteMode("avoid")
    return boxes


def test_apply_layout_moves_shapes_and_reroutes(wx_app):
    frame, canvas = _make_canvas(wx_app)
    boxes = _chain(canvas, 5)
    before = [(min(b.x), min(b.y)) for b in boxes]
    result = canvas.ApplyLayout("spring", options={"spacing": 40, "seed": 1})
    assert len(result.positions) == 5
    assert "crossings" in result.metadata
    assert result.metadata["crossings"] <= result.metadata["crossings_before"]
    after = [(min(b.x), min(b.y)) for b in boxes]
    assert after != before
    # No overlaps after layout (spacing/2 gap enforced by the spring pass).
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax, ay = min(boxes[i].x), min(boxes[i].y)
            bx, by = min(boxes[j].x), min(boxes[j].y)
            assert ax + 100 <= bx or bx + 100 <= ax or ay + 60 <= by or by + 60 <= ay
    # Edges still connect their shapes (endpoints on the box perimeters).
    for line in [s for s in canvas.diagram.shapes if hasattr(s, "_from") and s._from]:
        assert len(line._lineControlPoints) >= 2
    frame.Destroy()


def test_apply_layout_deterministic(wx_app):
    def run_once():
        frame, canvas = _make_canvas(wx_app)
        boxes = _chain(canvas, 4)
        canvas.ApplyLayout("spring", options={"spacing": 40, "seed": 3})
        positions = [(min(b.x), min(b.y)) for b in boxes]
        frame.Destroy()
        return positions

    assert run_once() == run_once()


def test_diagram_apply_layout_headless():
    diagram = wxdiagram.Diagram()
    boxes = []
    for i in range(3):
        box = wxdiagram.Block()
        box.x = [i * 5, i * 5 + 100]
        box.y = [i * 5, i * 5 + 60]
        diagram.AddShape(box)
        boxes.append(box)
    result = diagram.ApplyLayout("spring", options={"spacing": 30, "seed": 1})
    assert len(result.positions) == 3
    assert {(min(b.x), min(b.y)) for b in boxes} != {(0, 0), (5, 5), (10, 10)}


def test_route_edges_refreshes_straight_edges(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(300, 0, 380, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    assert line.GetRouteMode() == "straight"
    before = line.GetEnds()
    b.move_to(500, 200)  # bypass MoveLinks, as a batch operation might
    canvas.RouteEdges()
    assert line.GetEnds() != before
    frame.Destroy()


def test_route_mode_and_router_persist(wx_app, tmp_path):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    line.SetRouteMode("curved")

    path = tmp_path / "routed.json"
    canvas.diagram.Save(str(path))
    data = persistence.diagram_to_dict(canvas.diagram)
    line_data = next(s for s in data["shapes"] if s.get("routeMode"))
    assert line_data["routeMode"] == "curved"

    loaded = wxdiagram.Diagram.Load(str(path))
    loaded_line = next(s for s in loaded.shapes if hasattr(s, "_lineControlPoints"))
    assert loaded_line.GetRouteMode() == "curved"
    frame.Destroy()


def test_old_files_without_route_mode_load(wx_app, tmp_path):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    assert line.GetRouteMode() == "straight"
    path = tmp_path / "plain.json"
    canvas.diagram.Save(str(path))
    import json

    raw = json.loads(path.read_text())
    for shape in raw["shapes"]:
        shape.pop("routeMode", None)
        shape.pop("router", None)
    path.write_text(json.dumps(raw))
    loaded = wxdiagram.Diagram.Load(str(path))
    loaded_line = next(s for s in loaded.shapes if hasattr(s, "_lineControlPoints"))
    assert loaded_line.GetRouteMode() == "straight"
    frame.Destroy()
