"""Layout + routing playground.

Run from the repo root::

    uv run python -m wxdiagram.layoutdemo
    ./bin/run-layout

Builds a small graph on a wxdiagram canvas, runs the built-in spring layout,
lets you switch per-edge route modes, randomise shape sizes, and reset the
graph.  It is independent of pynsource: use it as a smoke test and as a
copy-paste source for custom layouts.

Router injection is an experimental API and is deliberately not exposed in
this playground yet.
"""

import random

import wx

import wxdiagram


def make_box(label, left, top, width=150, height=70):
    box = wxdiagram.Block()
    box.SetSize(width, height)
    box.move_to(left, top)
    box.label = label
    return box


class LayoutDemoFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wxdiagram - layout + routing playground", size=(1000, 700))
        panel = wx.Panel(self)
        self.canvas = wxdiagram.ShapeCanvas(panel)
        self.canvas.SetBackgroundColour(wx.WHITE)
        self.canvas.SetDiagram(wxdiagram.Diagram())

        self.route_choice = wx.Choice(
            panel, choices=["straight", "auto", "avoid", "curved", "orthogonal"]
        )
        self.route_choice.SetSelection(1)  # auto
        reset_btn = wx.Button(panel, label="Reset")
        layout_btn = wx.Button(panel, label="Run spring layout")
        add_btn = wx.Button(panel, label="Add random boxes")
        randomise_btn = wx.Button(panel, label="Randomise sizes")
        route_btn = wx.Button(panel, label="Apply route mode")
        self.reduce_crossings = wx.CheckBox(panel, label="Reduce crossings")
        self.reduce_crossings.SetValue(True)
        self.status = wx.StaticText(panel, label="ready")

        reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        layout_btn.Bind(wx.EVT_BUTTON, self.on_layout)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        randomise_btn.Bind(wx.EVT_BUTTON, self.on_randomise_sizes)
        route_btn.Bind(wx.EVT_BUTTON, self.on_route_mode)
        # Apply immediately on selection too: seeing "auto" in the dropdown
        # should mean the edges really are in auto mode.
        self.route_choice.Bind(wx.EVT_CHOICE, self.on_route_mode)

        action_row = wx.BoxSizer(wx.HORIZONTAL)
        for widget in (reset_btn, layout_btn, add_btn, randomise_btn, self.reduce_crossings):
            action_row.Add(widget, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)

        route_row = wx.BoxSizer(wx.HORIZONTAL)
        for widget in (
            wx.StaticText(panel, label=" route:"),
            self.route_choice,
            route_btn,
        ):
            route_row.Add(widget, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(action_row, 0, wx.EXPAND)
        sizer.Add(route_row, 0, wx.EXPAND)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.status, 0, wx.ALL, 4)
        panel.SetSizer(sizer)

        self._seed_graph()

    def _seed_graph(self):
        boxes = [make_box(f"node {i}", 50 + (i % 4) * 220, 50 + (i // 4) * 170) for i in range(8)]
        for box in boxes:
            self.canvas.InsertShape(box, 999)
        links = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (6, 7), (1, 5), (3, 7)]
        mode = self.route_choice.GetStringSelection()
        for a, b in links:
            line = self.canvas.join_shapes(boxes[a], boxes[b])
            line.SetRouteMode(mode)
        self.canvas.update_virtual_size()

    def on_reset(self, _event):
        """Rebuild the original graph (and its layout) from scratch."""
        self.canvas.deselect()
        self.canvas.SetDiagram(wxdiagram.Diagram())
        self.route_choice.SetSelection(1)  # auto
        self._seed_graph()
        try:
            self.canvas.ZoomToFit()
        except Exception:
            pass
        self.canvas.Refresh()
        self.status.SetLabel("reset")

    def on_add(self, _event):
        letters = "ABCDEFGH"
        for _ in range(3):
            box = make_box(
                "new " + random.choice(letters),
                random.uniform(0, 600),
                random.uniform(0, 400),
            )
            self.canvas.InsertShape(box, 999)
            shapes = [
                s
                for s in self.canvas.diagram.shapes
                if getattr(s, "_from", None) is None and not hasattr(s, "_lineControlPoints")
            ]
            if len(shapes) >= 2:
                other = random.choice([s for s in shapes if s is not box] or shapes)
                line = self.canvas.join_shapes(other, box)
                line.SetRouteMode(self.route_choice.GetStringSelection())
        self.canvas.update_virtual_size()
        self.canvas.Refresh()
        self._run_layout()

    def _layout_options(self):
        return {
            "spacing": 40,
            "seed": 1,
            "reduce_crossings": self.reduce_crossings.GetValue(),
        }

    def _run_layout(self):
        result = self.canvas.ApplyLayout("spring", options=self._layout_options())
        meta = result.metadata or {}
        before = meta.get("crossings_before")
        after = meta.get("crossings")
        count = len(result.positions)
        if before == after:
            self.status.SetLabel(f"spring: {count} nodes, crossings {after}")
        else:
            self.status.SetLabel(f"spring: {count} nodes, crossings {before} -> {after}")
        return result

    def on_randomise_sizes(self, _event):
        """Give every node a random size, keeping its centre point."""
        widths = [80, 110, 140, 180, 220, 260]
        heights = [50, 70, 90, 120, 160]
        for shape in list(self.canvas.diagram.shapes):
            if hasattr(shape, "_lineControlPoints") or getattr(shape, "_from", None) is not None:
                continue
            if not getattr(shape, "x", None) or not getattr(shape, "y", None):
                continue
            cx = (min(shape.x) + max(shape.x)) / 2.0
            cy = (min(shape.y) + max(shape.y)) / 2.0
            width = random.choice(widths)
            height = random.choice(heights)
            set_size = getattr(shape, "SetSize", None)
            if callable(set_size):
                try:
                    set_size(width, height)
                    shape.move_center(cx, cy)
                    continue
                except Exception:
                    pass
            # Fallback for shapes without SetSize (e.g. composites): resize
            # their bounding points in place.
            shape.x = [cx - width / 2.0, cx + width / 2.0]
            shape.y = [cy - height / 2.0, cy + height / 2.0]
        self.canvas.RouteEdges()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()
        self.status.SetLabel("randomised sizes")

    def on_layout(self, _event):
        self._run_layout()
        try:
            self.canvas.ZoomToFit()
        except Exception:
            pass

    def on_route_mode(self, _event):
        mode = self.route_choice.GetStringSelection()
        for shape in self.canvas.diagram.shapes:
            if hasattr(shape, "SetRouteMode"):
                try:
                    shape.SetRouteMode(mode)
                except Exception:
                    pass
        self.canvas.Refresh()
        self.status.SetLabel(f"route mode: {mode}")


def main():
    app = wx.App(redirect=False)
    frame = LayoutDemoFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
