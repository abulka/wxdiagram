# Tutorial 1 — Canvas and shapes

A complete little app: a canvas, four kinds of shape, colours and selection.

```python
import wx

import wxdiagram


class Frame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wxdiagram tutorial 1", size=(900, 620))
        self.canvas = wxdiagram.ShapeCanvas(self)
        self.canvas.SetDiagram(wxdiagram.Diagram())

        client = wxdiagram.Block()
        client.label = "Client"
        client.x = [40, 200]
        client.y = [60, 150]

        controller = wxdiagram.Block()
        controller.label = "UserController"
        controller.SetBrush(wx.Brush("LIGHT BLUE"))
        controller.x = [330, 560]
        controller.y = [40, 220]

        ellipse = wxdiagram.ConnectableEllipseShape()
        ellipse.SetBrush(wx.Brush("PALE GREEN"))
        ellipse.x = [620, 800]
        ellipse.y = [60, 180]

        diamond = wxdiagram.PolygonShape()
        diamond.Create([(0, -60), (80, 0), (0, 60), (-80, 0)])
        diamond.SetBrush(wx.Brush("LIGHT YELLOW"))
        diamond.move_to(720, 300)

        for shape in (client, controller, ellipse, diamond):
            self.canvas.InsertShape(shape, 999)

        self.canvas.update_virtual_size()
        self.canvas.ZoomToFit()
        self.Show()


app = wx.App(redirect=False)
Frame()
app.MainLoop()
```

What to try:

- **Click** a shape to select it. Rectangles, ellipses and polygons show eight
  resize handles: corner drags keep the aspect ratio (Shift frees it, Alt
  resizes from the centre), edge drags change one axis.
- **Drag empty canvas** to marquee-select; Shift/Ctrl adds to the selection.
- **Arrow keys** nudge; **Delete** removes; **Ctrl+Z** undoes; **Ctrl+A**
  selects all; **Tab** cycles.
- **Polygons** are hit-tested over their whole interior, not just the outline.

## Adding your own colours

Every shape has `SetPen()` / `SetBrush()`:

```python
shape.SetPen(wx.Pen(wx.BLACK, 2))
shape.SetBrush(wx.Brush(wx.Colour(250, 240, 200)))
```

A shape without an explicit brush uses `shape.fill` (a colour name, `"WHITE"`
by default). You can also build classic OGL-style colours by assigning
`shape.pen = ["BLACK", 1]` and `shape.fill = ["YELLOW"]` before the first
paint.

## Canvas settings worth knowing

```python
canvas.showGrid = True            # draw a grid
canvas.snapToGrid = True          # snap drags to it
canvas.diagram.SetGridSpacing(20)
canvas.alignmentGuides = False    # turn off magnetic edges/centres
```
