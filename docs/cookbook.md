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

## Edge routing

```python
line = canvas.join_shapes(a, b)
line.autoRoute = True        # avoid obstacles (straight when clear)
line.autoRoute = "curved"    # always bow the edge (free bezier)
line.UpdateRoute()           # "straight", "curved" or "orthogonal"

line.SetRouteMode("straight")  # or "avoid" / "curved" at runtime
line.GetRouteMode()
```

`route_edge(p1, p2, obstacle_rects)` (also `wxdiagram.route_edge`) is a pure
function: it returns control points plus the style used.  A clear segment stays
straight; otherwise the edge bows into a spline, and if curves are blocked it
takes an orthogonal lane outside the obstacles.  The router knows nothing about
layout - pass it the rectangles to avoid.

Parallel edges between the same two shapes are spread into separate lanes
(14 diagram units apart) automatically by `LineShape.autoRoute`; pass `spread`
to `route_edge` directly if you route yourself.

## Edge labels

```python
line = canvas.join_shapes(client, controller)   # join_shapes returns the line
line.AddText("uses")                            # middle label
line.SetLabelPosition(0, 0, -12)                # nudge it off the line
```

Region indices: 0 = middle, 1 = near the start, 2 = near the end.
`SetLabelText(index, text)` replaces the text (multi-line via `\n`).  Labels
are stored with the shape's regions, so they save and load with the diagram.

## Scrolling speed

```python
canvas.WHEEL_SCROLL_PIXELS = 20        # Windows/Linux: pixels per notch
canvas.WHEEL_SCROLL_PIXELS_MACOS = 1.0 # macOS: multiplier on wxOSX deltas
canvas.WHEEL_MAX_STEP = 80             # clamp for one wheel event
```

> macOS is special: wxOSX sets the wheel delta to 10 and forwards the precise
> trackpad deltas, so they are already close to pixels.  Do not scale them by
> the notch size or trackpad scrolling becomes ~20× too fast.

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
