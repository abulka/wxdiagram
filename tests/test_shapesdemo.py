"""Smoke tests for the shapesdemo editor (frame, panel states, save/load)."""

import wx

from wxdiagram import persistence, shapesdemo


def _make_frame(wx_app):
    frame = shapesdemo.ShapesDemoFrame()
    frame.Show()
    wx.Yield()
    return frame


def test_frame_seeds_scene(wx_app):
    frame = _make_frame(wx_app)
    assert len(frame.canvas.diagram.shapes) == 5
    frame.Destroy()


def test_add_each_kind(wx_app):
    frame = _make_frame(wx_app)
    before = len(frame.canvas.diagram.shapes)
    for kind in ("Rectangle", "Circle", "Ellipse", "Triangle", "Line"):
        shape = frame.AddShapeOfKind(kind)
        assert shape is not None
        assert shape.GetName().startswith(kind)
    assert len(frame.canvas.diagram.shapes) == before + 5
    frame.Destroy()


def test_panel_states_do_not_crash(wx_app):
    frame = _make_frame(wx_app)
    a = frame.AddShapeOfKind("Rectangle")
    b = frame.AddShapeOfKind("Circle")
    frame.canvas.deselect()
    frame.panel.RefreshPanel()
    frame.canvas.select(a)
    wx.Yield()
    frame.canvas.select(b)
    wx.Yield()
    group = frame.canvas.group_selected()
    assert group is not None
    wx.Yield()
    frame.canvas.deselect()
    frame.canvas.select(group)
    wx.Yield()
    frame.Destroy()


def test_connect_and_edge_panel(wx_app):
    frame = _make_frame(wx_app)
    a = frame.AddShapeOfKind("Rectangle")
    b = frame.AddShapeOfKind("Ellipse")
    frame.canvas.deselect()
    frame.canvas.select(a)
    frame.canvas.select(b)
    frame.OnConnect(None)
    edges = [s for s in frame.canvas.diagram.shapes if shapesdemo._is_attached_edge(s)]
    assert len(edges) == 1
    frame.canvas.deselect()
    frame.canvas.select(edges[0])
    wx.Yield()
    frame.Destroy()


def test_demo_save_load_round_trip(wx_app, tmp_path):
    frame = _make_frame(wx_app)
    a = frame.AddShapeOfKind("Rectangle")
    b = frame.AddShapeOfKind("Triangle")
    frame.canvas.deselect()
    frame.canvas.select(a)
    frame.canvas.select(b)
    frame.canvas.group_selected()
    path = tmp_path / "demo.json"
    persistence.save(frame.canvas.diagram, path)
    loaded = persistence.load(str(path))
    assert len(loaded.shapes) == len(frame.canvas.diagram.shapes)
    second = tmp_path / "demo2.json"
    persistence.save(loaded, second)
    import json

    assert json.loads(path.read_text()) == json.loads(second.read_text())
    frame.Destroy()


def test_panel_wraps_without_horizontal_overflow(wx_app):
    frame = _make_frame(wx_app)
    panel = frame.panel
    # Wide window first.
    frame.SetSize((1200, 760))
    frame.Layout()
    for _ in range(6):
        wx.Yield()
    panel._relayout()
    wide_client = panel.scrolled.GetClientSize().width
    assert panel.scrolled.GetVirtualSize().width <= wide_client + 2

    # Now make the frame narrow enough that the inspector is constrained.
    frame.SetSize((700, 760))
    frame.Layout()
    for _ in range(6):
        wx.Yield()
    panel._relayout()
    narrow_client = panel.scrolled.GetClientSize().width
    assert narrow_client < wide_client
    assert panel.scrolled.GetVirtualSize().width <= narrow_client + 2
    # Long help text must actually be wrapped, not left as one line.
    tips = [label for label in panel._wrappers if "Quick tips" in label._base_text]
    assert tips
    assert "\n" in tips[0].GetLabel()
    assert tips[0].GetBestSize().width <= narrow_client
    frame.Destroy()


def test_theme_switch_updates_canvas_and_panel(wx_app):
    frame = _make_frame(wx_app)
    panel = frame.panel

    frame.theme_name = "dark"
    frame._apply_theme()
    wx.Yield()
    assert frame.canvas.GetBackgroundColour().GetLuminance() < 0.35
    assert panel.GetBackgroundColour().GetLuminance() < 0.35
    assert panel.scrolled.GetBackgroundColour().GetLuminance() < 0.35

    frame.theme_name = "light"
    frame._apply_theme()
    wx.Yield()
    assert frame.canvas.GetBackgroundColour().GetLuminance() > 0.7
    assert panel.GetBackgroundColour().GetLuminance() > 0.7
    assert panel.GetBackgroundColour() != panel.scrolled.GetBackgroundColour()

    frame.theme_name = "system"
    frame._apply_theme()
    wx.Yield()
    assert frame.palette in (shapesdemo.LIGHT_THEME, shapesdemo.DARK_THEME)
    frame.Destroy()


def test_sash_is_wide_and_visible(wx_app):
    frame = _make_frame(wx_app)
    sash = frame.panel.sash
    assert sash.GetSize().width >= 10
    assert sash.palette["sash_line"] != sash.palette["sash_bg"]
    frame.Destroy()


def _mouse(canvas, wx_type, diagram_xy, down=False):
    client = canvas.diagram_point_to_client_coords(*diagram_xy)
    event = wx.MouseEvent(wx_type)
    event.SetPosition(wx.Point(int(client[0]), int(client[1])))
    event.SetX(int(client[0]))
    event.SetY(int(client[1]))
    event.SetEventObject(canvas)
    if down:
        event.SetLeftDown(True)
    return event


def test_connection_feedback_and_edge_colours_follow_theme(wx_app):
    from wxdiagram.core import ConnectionHandleNode, ConnectionShape

    frame = _make_frame(wx_app)
    frame.theme_name = "dark"
    frame._apply_theme()
    wx.Yield()
    canvas = frame.canvas
    a = frame.AddShapeOfKind("Rectangle", centre=(200, 200))
    b = frame.AddShapeOfKind("Ellipse", centre=(600, 300))
    canvas.deselect()
    wx.Yield()

    start = a.connection_points()["right"]
    canvas.GetEventHandler().ProcessEvent(_mouse(canvas, wx.wxEVT_MOTION, start, down=False))
    canvas.GetEventHandler().ProcessEvent(_mouse(canvas, wx.wxEVT_LEFT_DOWN, start))
    target = (b.GetX(), b.GetY())
    canvas.GetEventHandler().ProcessEvent(_mouse(canvas, wx.wxEVT_MOTION, target, down=True))
    wx.Yield()

    # The temporary line is light enough to see, and the drop target shows dots.
    temp = [s for s in canvas.diagram.shapes if isinstance(s, ConnectionShape)]
    assert temp
    assert temp[0]._pen is not None
    assert temp[0]._pen.GetColour().GetLuminance() > 0.4
    dots = [n for n in canvas.nodes if isinstance(n, ConnectionHandleNode)]
    assert len(dots) == 4
    assert canvas._hover_shape is b

    # Even a fraction outside the target shape, near a dot, keeps the dots.
    near_right = b.connection_points()["right"]
    canvas.GetEventHandler().ProcessEvent(
        _mouse(canvas, wx.wxEVT_MOTION, (near_right[0] + 6, near_right[1]), down=True)
    )
    wx.Yield()
    assert len([n for n in canvas.nodes if isinstance(n, ConnectionHandleNode)]) == 4
    assert canvas._hover_shape is b

    canvas.GetEventHandler().ProcessEvent(_mouse(canvas, wx.wxEVT_LEFT_UP, target))
    wx.Yield()
    edges = [s for s in canvas.diagram.shapes if shapesdemo._is_attached_edge(s)]
    assert len(edges) == 1
    edge = edges[0]
    assert edge.GetPenColour().GetLuminance() > 0.4

    # Switching to light mode re-tints the default edge so it stays visible.
    frame.theme_name = "light"
    frame._apply_theme()
    wx.Yield()
    assert edge.GetPenColour().GetLuminance() < 0.4
    frame.Destroy()


def test_triangle_uses_fill_and_shape_controls(wx_app):
    """PolygonShape is a LinesShape subclass, but it is not a free line."""
    frame = _make_frame(wx_app)
    triangle = frame.AddShapeOfKind("Triangle")
    assert not shapesdemo._is_free_line(triangle)
    fill = triangle.GetFillColour()
    assert (fill.Red(), fill.Green(), fill.Blue()) != (255, 255, 255)
    frame.canvas.deselect()
    frame.canvas.select(triangle)
    wx.Yield()
    assert "size" in frame.panel._controls
    assert "line_points" not in frame.panel._controls
    frame.Destroy()


def test_flat_button_click_adds_shape(wx_app):
    frame = _make_frame(wx_app)
    panel = frame.panel
    buttons = []

    def walk(window):
        for child in window.GetChildren():
            if isinstance(child, shapesdemo.FlatButton):
                buttons.append(child)
            walk(child)

    walk(panel.scrolled)
    rectangle = next(button for button in buttons if button._label == "Rectangle")
    before = len(frame.canvas.diagram.shapes)
    event = wx.MouseEvent(wx.wxEVT_LEFT_UP)
    event.SetPosition(wx.Point(5, 5))
    rectangle._on_up(event)
    wx.Yield()
    assert len(frame.canvas.diagram.shapes) == before + 1
    frame.Destroy()
