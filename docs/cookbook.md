# Cookbook

## Custom shape

Subclass `RectangleShape` and override `draw` for custom painting. Use the
same pen/brush conventions as the built-in shapes.

```python
class Badge(wxdiagram.RectangleShape):
    def draw(self, dc):
        super().draw(dc)
        dc.SetTextForeground(wx.RED)
        dc.DrawText("NEW", int(self.x[0]) + 4, int(self.y[0]) + 4)
```

## Use a spline edge

```python
line = wxdiagram.LineShape()
line.MakeLineControlPoints(4)
line.SetEnds(0, 0, 200, 100)
line.SetSpline(True)
line.AddArrow(wxdiagram.ARROW_ARROW)
canvas.AddShape(line)
```

## Zoom to fit

```python
canvas.ZoomToFit(margin=40)
```

## Keep labels out of the way

`TextShape` is a non-interactive caption: it is not hit-tested and never
blocks selection of the shapes around it.

```python
caption = wxdiagram.TextShape(20, 20, "Section heading", colour="GRAY")
canvas.AddShape(caption)
```

## Programmatic selection

```python
canvas.select(shape)          # add to the selection
canvas.getSelectedShapes()    # list of selected shapes
canvas.deselect()             # clear
```
