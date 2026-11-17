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

To leave decoration out of the calculation, override `getContentBounds()`.
It returns `(max_x, max_y)` in diagram coordinates:

```python
class UmlCanvas(wxdiagram.ShapeCanvas):
    def getContentBounds(self):
        # only class boxes matter for fit-to-window, not captions or edges
        return self.box_bounds()
```

The scrollable area starts at `getContentOrigin()`, which by default is the
minimum x/y over all shapes (and composite children). That means content at
negative diagram coordinates is still reachable. Override it alongside
`getContentBounds()` if your canvas navigates a different region:

```python
    def getContentOrigin(self):
        return self.box_origin()      # (min_x, min_y)
```

## Grid and alignment guides

```python
canvas.showGrid = True            # draw the background grid
canvas.snapToGrid = True          # snap shape drags to it
canvas.diagram.SetGridSpacing(20) # diagram units (default 10)

canvas.alignmentGuides = True     # magnetic edges/centres (default on)
canvas.ALIGN_TOLERANCE = 4        # screen pixels
```

Hit-testing and drawing only; nothing is stored in the document.

## Export a PNG

```python
canvas.ExportPng("diagram.png", scale=2, margin=10)
```

Only the shapes are rendered (no handles, guides or marquee).  `scale`
multiplies diagram units and `margin` is an output-pixel border.

## Buffered painting

Platforms that do not composite their windows can flicker while dragging.  Opt
into a buffered paint pass:

```python
class MyCanvas(wxdiagram.ShapeCanvas):
    bufferedPainting = True
```

It uses `wx.AutoBufferedPaintDC` and sets `wx.BG_STYLE_PAINT` (the canvas then
erases its own background).

## Move by top-left coordinates

`Move` takes the shape centre. Layouts and saved positions usually use the
top-left corner, so use `MoveTo`. It also refreshes attached lines:

```python
shape.MoveTo(dc, node.left, node.top)   # dc may be None
```

## Manage scrolling yourself

Applications that already own the scrollbars can switch off the library's
automatic virtual size and mouse-wheel handling:

```python
canvas.autoVirtualSize = False   # don't resize scrollbars after shape changes
canvas.zoomInputEnabled = False  # don't handle Ctrl+wheel / pinch / drag-pan

# ...and handle the events in your subclass:
class AppCanvas(wxdiagram.ShapeCanvas):
    def OnMouseWheel(self, event):
        if event.ShiftDown():
            self.on_layout_wheel(event)   # application-specific
            return
        super().OnMouseWheel(event)       # Ctrl+wheel zoom, plain scrolling
```

## Keep labels out of the way

`TextShape` is a non-interactive caption: it is not hit-tested and never
blocks selection of the shapes around it.

```python
caption = wxdiagram.TextShape(20, 20, "Section heading", colour="GRAY")
canvas.AddShape(caption)
```

## Selecting and editing

- Plain drag on empty canvas draws a **marquee**; Shift/Ctrl adds to the selection.
- Esc clears the selection.
- Arrow keys nudge selected shapes by 1px; Shift+Arrow nudges by 10px.
- Ctrl+D duplicates the selection, Ctrl+Z / Ctrl+Shift+Z undo/redo.
- Alt/Space/middle-drag pans. Set `canvas.emptyDragMode = canvas.EMPTY_DRAG_PAN`
  if you want plain drag to pan instead.

Undo/redo snapshots the shape list and geometry by default. Applications with a
separate model can override `snapshot_state()` and `restore_state()` to snapshot
their own state (pynsource snapshots its graph model this way).

## Programmatic selection

```python
canvas.select(shape)          # add to the selection
canvas.getSelectedShapes()    # list of selected shapes
canvas.deselect()             # clear
```
