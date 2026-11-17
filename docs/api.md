# API reference

All public names are re-exported from `wxdiagram`; the sections below are
generated from the docstrings with mkdocstrings. If you are porting from
`wx.lib.ogl`, also read the [migration guide](migration-from-wx-lib-ogl.md).

## At a glance

| Area | Types |
|---|---|
| Canvas | `ShapeCanvas`, `Diagram` |
| Basic shapes | `Shape`, `RectangleShape`, `EllipseShape`, `PolygonShape`, `LinesShape` |
| Interactive shapes | `Block`, `ResizableRectangleShape`, `ConnectableEllipseShape`, `DividedShape`, `CompositeShape`, `SelectableTextShape` |
| Edges | `LineShape`, `ConnectionShape`, `ArrowHead` |
| Bitmaps | `BitmapShape`, `ResizableBitmapShape` |
| Mixins | `Selectable`, `Resizeable`, `Connectable`, `Attributable` |
| Routing | `wxdiagram.routing.route_edge`, `LineShape.SetRouteMode` |
| Persistence | `wxdiagram.persistence.save`, `wxdiagram.persistence.load` |

## Canvas

### ShapeCanvas

The scrolled window that owns selection, zoom/pan, routing defaults and
repainting. Pass it a `Diagram` with `SetDiagram()`.

::: wxdiagram.ShapeCanvas
    options:
      members:
        - AddShape
        - InsertShape
        - AppendShape
        - DeleteShape
        - AddImage
        - join_shapes
        - select
        - deselect
        - getSelectedShapes
        - update_virtual_size
        - ZoomIn
        - ZoomOut
        - ZoomTo
        - ZoomReset
        - ZoomToFit
        - CenterOn
        - Snap
        - ExportPng
        - getContentBounds
        - getContentOrigin
        - snapshot_state
        - restore_state
        - undo
        - redo
        - duplicate_selected
        - delete_selected
        - bring_to_front
        - send_to_back
        - bring_forward
        - send_backward
      show_source: false

Canvas settings you are likely to tune (class or instance attributes):

| Attribute | Default | Purpose |
|---|---|---|
| `autoVirtualSize` | `True` | keep the scrollbars in sync with the shapes |
| `zoomInputEnabled` | `True` | handle Ctrl+wheel and pinch |
| `panOnDrag` | `True` | Alt/Space/middle-drag pans |
| `emptyDragMode` | `"marquee"` | plain drag on empty canvas: `"marquee"` or `"pan"` |
| `zoomAnchor` | `"mouse"` | `"mouse"`, `"selection"` or `"center"` |
| `bringClickedShapeToFront` | `True` | raise shapes when clicked |
| `showGrid` | `False` | draw the diagram grid |
| `snapToGrid` | `False` | snap drags to the grid |
| `alignmentGuides` | `True` | magnetic guides to other shapes |
| `bufferedPainting` | `False` | use `AutoBufferedPaintDC` |
| `WHEEL_SCROLL_PIXELS` | `20` | wheel pixels per notch (Windows/Linux) |
| `WHEEL_SCROLL_PIXELS_MACOS` | `1.0` | multiplier on wxOSX's precise deltas |
| `PAN_START_THRESHOLD` | `3` | pixels before a drag becomes a pan |
| `DRAG_TOLERANCE` | `3` | pixels before a shape move/resize starts |

### Diagram

The shape list plus grid/snap and save/load helpers.

::: wxdiagram.Diagram
    options:
      show_source: false

## Shapes

### Shape

Base class: point lists (`x`, `y`), pen/brush, attached lines, canvas
attachment, copying.

::: wxdiagram.Shape
    options:
      show_source: false

### RectangleShape

::: wxdiagram.RectangleShape
    options:
      show_source: false

### Block

A labelled, connectable rectangle (the common "box" shape).

::: wxdiagram.Block
    options:
      show_source: false

### ResizableRectangleShape

::: wxdiagram.ResizableRectangleShape
    options:
      show_source: false

### EllipseShape

::: wxdiagram.EllipseShape
    options:
      show_source: false

### ConnectableEllipseShape

::: wxdiagram.ConnectableEllipseShape
    options:
      show_source: false

### PolygonShape

A closed polygon; hit-testing covers its interior.

::: wxdiagram.PolygonShape
    options:
      show_source: false

### LinesShape

An open polyline through a list of points.

::: wxdiagram.LinesShape
    options:
      show_source: false

### DividedShape

A rectangle split into regions (the UML class-box look).

::: wxdiagram.DividedShape
    options:
      show_source: false

### CompositeShape

A rectangle that owns child shapes and constraints.  Resizing the frame
scales the children with it.

::: wxdiagram.CompositeShape
    options:
      show_source: false

### BitmapShape / ResizableBitmapShape

::: wxdiagram.BitmapShape
    options:
      show_source: false

::: wxdiagram.ResizableBitmapShape
    options:
      show_source: false

### TextShape / SelectableTextShape

::: wxdiagram.TextShape
    options:
      show_source: false

::: wxdiagram.SelectableTextShape
    options:
      show_source: false

## Edges

### LineShape

Attached or free lines, arrowheads, splines, bends, labels and routing modes.

::: wxdiagram.LineShape
    options:
      members:
        - AddArrow
        - ClearArrowsAtPosition
        - DeleteArrowHead
        - GetArrowHead
        - AddText
        - SetLabelText
        - GetLabelPosition
        - SetLabelPosition
        - SetRouteMode
        - GetRouteMode
        - UpdateRoute
        - ResetRoute
        - SetSpline
        - IsSpline
        - Straighten
        - MakeLineControlPoints
        - SetEnds
        - GetEnds
      show_source: false

Routing modes accepted by `SetRouteMode`:

| Mode | Behaviour |
|---|---|
| `"straight"` | always a straight line |
| `"auto"` | straight when clear, a curve around boxes; never orthogonal |
| `"avoid"` | straight, curve, then an orthogonal L/Z fallback |
| `"curved"` | always a free curve |
| `"orthogonal"` | always a stub + L/Z orthogonal route |

### ConnectionShape

The transient line drawn while dragging from an output port to an input port.

::: wxdiagram.ConnectionShape
    options:
      show_source: false

### Arrow constants

| Constant | Meaning |
|---|---|
| `ARROW_ARROW` | solid triangle |
| `ARROW_DOUBLE_OBLIQUE` | open double line |
| `ARROW_SINGLE_OBLIQUE` | open single line |
| `ARROW_FILLED_CIRCLE` | filled circle |
| `ARROW_HOLLOW_CIRCLE` | hollow circle |
| `ARROW_POSITION_START` / `MIDDLE` / `END` | where on the line the head sits |

## Mixins

::: wxdiagram.Selectable
    options:
      show_source: false

::: wxdiagram.Resizeable
    options:
      show_source: false

::: wxdiagram.Connectable
    options:
      show_source: false

::: wxdiagram.Attributable
    options:
      show_source: false

## Routing

`route_edge` is the pure routing function used by `LineShape`; it has no wx
dependency, so it can be reused by a layout or a custom edge.

::: wxdiagram.routing.route_edge
    options:
      show_source: false

## Persistence

::: wxdiagram.persistence.save
    options:
      show_source: false

::: wxdiagram.persistence.load
    options:
      show_source: false
