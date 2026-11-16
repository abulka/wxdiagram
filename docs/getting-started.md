# Getting started

## Install

Requires Python 3.10+ and wxPython 4.2+.

```bash
pip install wxdiagram
```

From source with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/abulka/wxdiagram.git
cd wxdiagram
uv sync
```

## Hello canvas

```python
import wx
import wxdiagram

app = wx.App(redirect=False)
frame = wx.Frame(None, title="wxdiagram minimal", size=(600, 400))

canvas = wxdiagram.ShapeCanvas(frame)
canvas.SetDiagram(wxdiagram.Diagram())

shape = wxdiagram.RectangleShape(100, 100, 300, 200)
shape.AddText("hello world")
canvas.InsertShape(shape, 999)

frame.Show()
canvas.update_virtual_size()
app.MainLoop()
```

## Connect two shapes

```python
left = wxdiagram.Block()
left.label = "Left"
canvas.AddShape(left)

right = wxdiagram.Block()
right.label = "Right"
canvas.AddShape(right)

canvas.join_shapes(left, right)
```

The edge is attached to both shapes and routed through their perimeters, so it
follows them when they move.

## Save and load

```python
diagram.Save("diagram.json")
loaded = wxdiagram.Diagram.Load("diagram.json")
canvas.SetDiagram(loaded)
```

## Run the demo

```bash
uv run python -m wxdiagram.demo
```
