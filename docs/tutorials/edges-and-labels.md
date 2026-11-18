# Tutorial 2 — Edges, labels and arrows

Edges are ordinary shapes with endpoints attached to two other shapes.  Their
endpoints are clipped to the shapes' perimeters, so they re-route as the
shapes move.

```python
import wx

import wxdiagram


class Frame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wxdiagram tutorial 2", size=(900, 620))
        self.canvas = wxdiagram.ShapeCanvas(self)
        self.canvas.SetDiagram(wxdiagram.Diagram())

        source = wxdiagram.Block()
        source.label = "Client"
        source.x = [50, 220]
        source.y = [80, 180]

        target = wxdiagram.Block()
        target.label = "UserService"
        target.x = [550, 800]
        target.y = [120, 260]

        self.canvas.InsertShape(source, 999)
        self.canvas.InsertShape(target, 999)

        line = self.canvas.join_shapes(source, target)
        line.SetRouteMode("auto")          # straight, or a curve around boxes
        line.AddArrow(
            wxdiagram.ARROW_ARROW,
            wxdiagram.ARROW_POSITION_END,
            size=12.0,
        )
        line.AddText("uses")
        line.SetLabelPosition(0, 0, -14)   # lift the label off the line

        self.canvas.update_virtual_size()
        self.canvas.ZoomToFit()
        self.Show()


app = wx.App(redirect=False)
Frame()
app.MainLoop()
```

## Connecting interactively

Drag from a round side dot on one shape to another shape; the target shows
four round drop dots while you drag.  `ShapeCanvas.join_shapes()` receives an
`edge_type` based on the modifier held at release:

| Modifier | `edge_type` |
|---|---|
| none | `association` |
| `Shift` | `generalisation` |
| `Alt` / `Option` | `composition` |

The base canvas treats these as plain attached lines; applications such as
[pynsource](https://github.com/abulka/pynsource) override `join_shapes()` to draw the matching UML relationship.

## Routing modes

| Mode | Use it for |
|---|---|
| `straight` | exact straight edges |
| `auto` | straight when clear, curved when a box blocks it |
| `avoid` | like `auto`, but may fall back to an orthogonal L/Z detour |
| `curved` | always a free curve |
| `orthogonal` | always an orthogonal route |

```python
line.SetRouteMode("curved")
line.GetRouteMode()          # "curved"
```

`SetRouteMode` re-routes immediately; the default is `False`/`straight` for a
fresh `LineShape`.

## Labels

Each line has three label slots: middle, start and end.

```python
line.SetLabelText(0, "middle label")
line.SetLabelText(1, "start")
line.SetLabelText(2, "end")
line.SetLabelPosition(0, 0, -16)   # offset from the middle anchor
```

Labels live in the line's regions, so they are saved with the diagram, and
clicking a label selects the edge.

## Free lines, bends and splines

`join_shapes` is for attached edges.  For drawing tools, create a `LineShape`
and drive its control points:

```python
from wxdiagram import LineShape

free = LineShape()
free.MakeLineControlPoints(3)       # endpoints + one midpoint
free.SetEnds(80, 400, 480, 400)
free.SetControlPoint(1, 280, 480)   # bend/spline midpoint
free.SetSpline(True)                # smooth curve through the points
free.AddArrow(wxdiagram.ARROW_ARROW, wxdiagram.ARROW_POSITION_END, size=12)
canvas.AddShape(free)
```

`GetControlPoints()` returns the current points.  Multi-point lines get one
editable resize handle per control point when selected.

## Arrow types

`ARROW_ARROW`, `ARROW_DOUBLE_OBLIQUE`, `ARROW_SINGLE_OBLIQUE`,
`ARROW_FILLED_CIRCLE` and `ARROW_HOLLOW_CIRCLE`, at `ARROW_POSITION_START`,
`ARROW_POSITION_MIDDLE` or `ARROW_POSITION_END`.  A line can carry several.
