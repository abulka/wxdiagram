# Tutorial 3 — Images, composites and export

## Importing an image

`AddImage` loads the file, scales it down to `max_size` if needed, centres it
in the viewport and returns a `ResizableBitmapShape`:

```python
shape = canvas.AddImage(
    "photo.jpg",
    max_size=(600, 400),
    center=True,
    send_to_back=True,        # keep it behind the diagram
)
```

The bitmap is stretched from the original at paint time, so dragging a handle
stays in step with the mouse at any zoom.  Select it and use the eight handles,
or `shape.ResetSize()` (also on the right-click menu in the demo) to restore the
original dimensions.

## Composites

A `CompositeShape` groups children so they move — and when you resize the frame,
scale — together:

```python
comp = wxdiagram.CompositeShape()

for label, left, top in (("A", 10, 10), ("B", 180, 10), ("C", 10, 100)):
    child = wxdiagram.Block()
    child.label = label
    child.x = [left, left + 140]
    child.y = [top, top + 70]
    comp.add_child(child)

comp.CalculateSize()
comp.move_to(600, 60)
canvas.InsertShape(comp, 999)
```

The frame is selectable and resizable; corner drags keep the aspect ratio by
default, and the children are mapped into the new rectangle.  Optional
`Constraint` objects (see `CompositeShape.AddSimpleConstraint`) are re-evaluated
after a resize.

## Export a PNG

`ExportPng` renders the diagram at any scale, with a border, excluding
selection handles and guides:

```python
canvas.ExportPng("diagram.png", scale=2.0, margin=20)
```

## Save and load

```python
diagram.Save("diagram.json")          # or canvas.diagram.Save(...)
diagram = wxdiagram.Diagram.Load("diagram.json")
canvas.SetDiagram(diagram)
canvas.update_virtual_size()
canvas.ZoomToFit()
```

The format is versioned JSON; no pickle.  Labels, colours, routes, bitmap
filenames and composite children are included.

## Viewport helpers

```python
canvas.ZoomToFit()          # frame everything
canvas.ZoomReset()          # 100%
canvas.ZoomTo(0.75)
canvas.CenterOn(shape.GetX(), shape.GetY())
canvas.ZoomIn(anchor="center")
```

Content at negative coordinates is scrollable: the scroll area starts at the
diagram's top-left content origin, so shapes moved or resized past `(0, 0)` are
still reachable.
