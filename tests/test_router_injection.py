"""Injectable edge routers: per-edge override, canvas default, batch hook."""

import wx
import pytest

import wxdiagram
from wxdiagram.routing import BaseRouter, RouteResult


class MidpointRouter(BaseRouter):
    name = "test-midpoint"

    def route(self, request):
        (x1, y1), (x2, y2) = request.start, request.end
        mid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0 - 25.0)
        return RouteResult(points=(request.start, mid, request.end), style="diagonal")


class BatchCounterRouter(MidpointRouter):
    name = "test-batch-counter"
    calls = []

    def route_many(self, requests):
        BatchCounterRouter.calls.append(len(requests))
        return {r.edge_id: self.route(r) for r in requests}


def _make_canvas(wx_app):
    frame = wx.Frame(None, size=(700, 500))
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


def test_default_router_round_trip(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    assert line.GetRouterName() is None
    assert line.GetEffectiveRouter().name == "default"
    frame.Destroy()


def test_set_router_by_instance_and_name(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    router = MidpointRouter()
    line.SetRouter(router)
    assert line.GetRouter() is router
    assert line.GetEffectiveRouter() is router
    line.SetRouter("test-midpoint" if "test-midpoint" in wxdiagram.available_routers() else router)
    frame.Destroy()


def test_custom_router_changes_route(wx_app):
    wxdiagram.register_router(MidpointRouter)
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    line.SetRouter("test-midpoint")
    style = line.UpdateRoute()
    assert style == "diagonal"
    assert len(line._lineControlPoints) == 3
    assert line._lineControlPoints[1][1] < 30.0  # lifted midpoint
    frame.Destroy()


def test_canvas_default_router_applies(wx_app):
    wxdiagram.register_router(MidpointRouter)
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    line.SetRouteMode("auto")
    canvas.SetDefaultRouter("test-midpoint")
    assert canvas.GetDefaultRouter() == "test-midpoint"
    styles = canvas.RouteEdges()
    assert list(styles.values()) == ["diagonal"]
    canvas.SetDefaultRouter(None)
    frame.Destroy()


def test_route_many_batch_hook(wx_app):
    wxdiagram.register_router(BatchCounterRouter)
    BatchCounterRouter.calls.clear()
    frame, canvas = _make_canvas(wx_app)
    boxes = [_block(i * 200, 0, i * 200 + 80, 60) for i in range(3)]
    for box in boxes:
        canvas.AddShape(box)
    for a, b in ((boxes[0], boxes[1]), (boxes[1], boxes[2])):
        line = canvas.join_shapes(a, b)
        line.SetRouteMode("auto")
    canvas.SetDefaultRouter("test-batch-counter")
    canvas.RouteEdges()
    assert BatchCounterRouter.calls == [2]
    frame.Destroy()


def test_auto_mode_never_produces_orthogonal(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    blocker = wxdiagram.RectangleShape(170, -150, 230, 200)
    canvas.AddShape(a)
    canvas.AddShape(b)
    canvas.AddShape(blocker)
    line = canvas.join_shapes(a, b)
    line.SetRouteMode("auto")
    style = line.UpdateRoute()
    assert style in ("straight", "curved")
    assert style != "orthogonal"
    frame.Destroy()


def test_unknown_router_name_fails_fast(wx_app):
    frame, canvas = _make_canvas(wx_app)
    a, b = _block(0, 0, 80, 60), _block(320, 0, 400, 60)
    canvas.AddShape(a)
    canvas.AddShape(b)
    line = canvas.join_shapes(a, b)
    with pytest.raises(KeyError):
        line.SetRouter("no-such-router-xyz")
    with pytest.raises(KeyError):
        canvas.SetDefaultRouter("no-such-router-xyz")
    frame.Destroy()
