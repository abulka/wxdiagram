# Changelog

## 0.2.3 — 2026-11-18

Interaction bug fixes found while exercising pynsource's sample diagram.

### Fixed

- Dragging a multi-selection that includes an attached edge no longer moves the
  edge directly as well as re-clipping it from its endpoint shapes.  The edge
  used to overshoot by the drag delta, stretching off-screen and expanding the
  virtual canvas; it now follows its shapes exactly.
- Dragging an attached edge on its own no longer detaches or shifts it.  Free
  (unattached) lines still move normally.
- `ShapeCanvas.SetDiagram()` clears the previous diagram's selection and
  selection handles, so stale resize/connection chrome is no longer painted on
  the new diagram until the next click.

## 0.2.2 — 2026-11-18

Shape-editor primitives plus a second demo proving them.

### Added

- Style and naming API on `Shape`: `GetName` / `SetName`, `GetFillColour` /
  `SetFillColour`, `GetPenColour` / `SetPenColour`, `GetPenWidth` /
  `SetPenWidth`. They work over both the modern `_pen` / `_brush` objects and
  the legacy `pen` / `fill` lists, and round-trip through JSON persistence.
- `CircleShape`: a connectable ellipse that stays circular while resizing
  (proportional handles only, four corner handles).
- `EllipseShape` now hit-tests a true ellipse and clips attached edges with
  `GetPerimeterPoint`.
- Connectable shapes now show **four corner resize handles plus four round side
  connection dots**.  Dots are clipped to the real perimeter (triangles use
  their sloping edges) and stay visible for the selected shape.  Dragging a dot
  and releasing anywhere over another connectable shape body creates an
  attached edge; `Connectable.connection_points()` exposes the dots and
  `showDropPorts` keeps the legacy drop ports available.
- `AddLine` / `RemoveLine` moved from `RectangleShape` to `Shape`, so ellipses,
  polygons and groups can be the source of an attached edge (fixes
  `AttributeError: ... has no attribute 'AddLine'` when connecting from an
  ellipse or triangle).
- `duplicate_selected()` places the copies on top of the z-order (previously
  they were inserted at the bottom).
- `PolygonShape` has a real bounding box (`GetBoundingBoxMin`), a bbox-centred
  `GetX` / `GetY`, a `GetPerimeterPoint` so attached edges meet its edges, and
  a `move_handle` that scales all vertices from the bounding box.  Its resize
  handles are now placed at bbox corners/edges, matching the indices the
  scaling code uses (previously they sat on vertices and moved the wrong
  geometry).
- `GroupShape` (in `wxdiagram.composite`): a composite that draws only its
  children, plus `ShapeCanvas.group_selected()` / `ungroup_selected()`.
  Attached lines stay top-level so edges keep following their endpoints.
- `ShapeCanvas.onSelectionChanged`: optional callback fired by `select()` /
  `deselect()`, for inspectors that live outside the canvas.
- Canvas chrome colours for theming: `handleFillColour`,
  `handleOutlineColour`, `portFillColour`, `portOutlineColour`,
  `marqueePenColour`, `connectionPenColour`, and `edgePenColour` /
  `edgePenWidth` for the default pen of new `join_shapes()` edges.
- While dragging a connection, the shape under the pointer shows its connection
  dots as drop targets.  The temporary line is theme-aware, so it stays visible
  against a dark canvas.
- Snapshot undo/redo now covers style, names, line control points, composite
  membership and edge endpoints — so recolour and group/ungroup are undoable.
- `wxdiagram.shapesdemo`: a Shape Studio-style editor
  (`uv run python -m wxdiagram.shapesdemo`) with a resizable properties panel
  (name, position, size, fill/border colours, border width, edge routing and
  arrowheads), grouping, File/Edit/Add/Arrange/View/Help menus and context
  menus.  The panel uses wrapping text, a responsive 2-column Add Shape grid and
  owner-drawn flat buttons that stay readable at narrow widths.  The splitter
  has a wide visible grip (macOS's native sash is only 1 px) and the inspector
  body is shaded separately from its header.  View > Theme switches between
  System, Light and Dark, including the canvas, grid, handles, connection dots,
  temporary connection line and default edge pen.
- Tests: `tests/test_shapes_primitives.py` (colour API, ellipse/polygon
  geometry, groups, style/group undo, selection callback, persistence) and
  `tests/test_shapesdemo.py` (frame smoke tests, panel wrapping, theme switch).

### Documentation

- New [layout tutorial](docs/tutorials/layout-and-routing.md) covering
  `ApplyLayout`, `RouteEdges`, engine options, fixed nodes, metrics and
  headless use.
- Expanded layout API reference and a layout heritage appendix explaining the
  pynsource ancestry, the deliberate differences and why the two engines
  remain separate.
- README, getting-started and contributing docs now list all three demos:
  kitchen sink (`wxdiagram.demo`), shape editor (`wxdiagram.shapesdemo`) and
  layout playground (`wxdiagram.layoutdemo`).

### Fixed

- Destination drop ports are now drawn as round dots, matching the round
  connection dots used to start an edge.  `INode` and `ONode` share the same
  port chrome helper as `ConnectionHandleNode`.
- Connecting two shapes no longer fails intermittently at fractional zoom.
  Connection dots are found by proximity even when an integer mouse coordinate
  lands a fraction outside the shape edge, and the drop target is resolved
  directly from connectable shapes rather than from whatever the temporary
  connection line happens to be under the pointer.
- The temporary connection line now starts at the side dot you grabbed
  (top/left/bottom as well as right), instead of always using the legacy right
  output port.
- Connection ports no longer disappear while dragging toward a target; the
  target's dots stay visible while the pointer is over the shape or near one
  of its dots.
- Releasing a connection over empty canvas (or the source shape) now removes
  the temporary line instead of leaving it floating.
- Moving an ellipse, polygon or any non-rectangle shape now re-routes its
  attached edges. `Shape.OnMoveLinks` is the shared implementation; previously
  only `RectangleShape` refreshed attached lines, so moving a target ellipse or
  triangle left the edge behind.
- `LineShapeBase.HitTest` and `LinesShape.HitTest` no longer divide by zero on
  zero-length or duplicate-point segments. Shape hit-tests are also guarded so
  a malformed shape cannot abort a connection drag.
- Deleting a shape now removes its attached edges (and cleans their endpoint
  references) instead of leaving floating edges behind; undo restores both the
  shapes and their edge attachments.
- Hit-testing during a drag cannot be derailed by an exception from an
  unrelated shape.

## 0.2.1 — 2026-11-17

The pynsource integration and interaction release.  This is the first upload
since 0.1.0: 0.2.0 was prepared but never published, so its changes are listed
here too.

Adds the small number of hooks the pynsource canvas needs, without pulling any
application code into the library, plus the interaction/routing work below.

### Added

- `Shape.MoveTo(dc, x, y)` — move by top-left coordinates and refresh attached
  lines. This replaces the `Move2` monkeypatch pynsource used to install.
- `ShapeCanvas.getContentBounds()` — overridable content bounds used by
  `ZoomToFit`. Applications can exclude edges or decoration from fit-to-window.
- Tests for the pynsource-facing API, `MoveTo`, overridable content bounds, and
  the `autoVirtualSize` / `zoomInputEnabled` opt-outs used by applications that
  manage their own scrollbars.
- Documented subclass pattern for handling Shift+wheel while delegating
  Ctrl+wheel zoom to the library.
- Marquee selection (plain drag on empty canvas), Shift/Ctrl additive marquee,
  Esc to clear, arrow-key nudge (Shift = 10px), duplicate, bring-to-front /
  send-to-back, and a snapshot-based undo/redo stack.
- Clicking a shape that is already selected keeps the multi-selection, so a
  drag moves the whole group (clicking an unselected shape still selects it).
- `bringClickedShapeToFront` (default True) controls whether clicking raises a
  shape; applications such as pynsource switch it off and use explicit z-order.
- `bring_forward()` and `send_backward()` alongside front/back.
- `ResizableBitmapShape` (rescaled bitmap on resize) and
  `ShapeCanvas.AddImage(path, max_size, center, send_to_back, shape_factory)`
  for consistent image import.
- `ShapeCanvas.delete_selected()` for one-step, undoable deletion.
- The demo is now a kitchen-sink app: File/Edit/Add/Arrange/View menus covering
  z-order, undo/redo, duplicate/delete, captions, bitmaps and image files, plus
  right-click context menus for shapes and empty canvas.
- Demo shape insertion now repaints immediately instead of waiting for mouse motion.
- `ResizableRectangleShape` (selectable/resizable plain rectangle) and
  `SelectableTextShape` (movable captions) added.
- `ResizableBitmapShape` now resizes when dragged by a handle and draws the
  original bitmap stretched in one blit, so high-resolution images keep up
  with the mouse instead of being rescaled on every motion.
- Resize handles stay under the cursor during a drag (hit-testing no longer
  lags behind the shape).
- Bitmap resizing keeps its geometry in floats instead of snapping to whole
  units, so the image tracks the mouse at any zoom level (integer snapping
  made it fall behind the pointer at fractional zoom, e.g. after zoom-to-fit).
- Handle positions are set when the handles are created, so a corner can be
  grabbed immediately after selecting a shape, before the next repaint.
- A bitmap resize handle stops at the opposite corner instead of flipping the
  image when dragged past it.
- Rectangles and blocks behave the same way: dragging a corner past the
  opposite one clamps instead of inverting the shape (which used to raise an
  assertion on the next hit-test).
- Corner resizing is proportional by default; hold Shift for free
  (non-proportional) resizing.
- Rectangle-like shapes now show eight resize handles: four corners plus four
  edge midpoints.  Edge handles resize a single axis; corners stay proportional.
- A resize finishes wherever the mouse is released, so the shape (not the
  invisible handle) stays selected when the pointer leaves the handle.
- Alt while dragging a resize handle grows/shrinks the shape from its centre.
- Shape drags and resizes ignore pointer movement below `DRAG_TOLERANCE`
  (3 px), so a click with a small hand tremor no longer nudges the shape.
- Grid and snapping (classic OGL API): `Diagram.SetGridSpacing()` /
  `GetGridSpacing()`, `SetSnapToGrid()` / `GetSnapToGrid()` and `Snap(x, y)`,
  plus `ShapeCanvas.Snap()` and the `showGrid` / `snapToGrid` flags.  The grid
  is drawn only when `showGrid` is on; snapping is off by default.
- Alignment guides: while dragging, a shape snaps to other rectangles' edges
  and centres within `ALIGN_TOLERANCE` (4 screen px) and dashed guide lines
  are drawn.  `alignmentGuides` turns it off.  Snapping is computed from the
  total drag offset, so a shape is not stuck to a guide as the pointer moves
  away.
- `ShapeCanvas.ExportPng(path, scale=1.0, margin=0)` renders the shapes (no
  handles, guides or marquee) to a PNG file; the demo's File menu has
  Export PNG.
- `bufferedPainting` opts into `wx.AutoBufferedPaintDC` (with
  `BG_STYLE_PAINT`) to reduce flicker on platforms that do not composite.
- macOS scrolling is no longer over-sensitive: wxOSX sets the wheel delta to 10
  and reports precise trackpad deltas, so normalising by the delta multiplied
  every event by 20.  macOS now scrolls by the reported deltas directly
  (`WHEEL_SCROLL_PIXELS_MACOS`), a single event is clamped to `WHEEL_MAX_STEP`,
  and x/y fractional remainders accumulate separately.
- Edge labels: `LineShape.AddText()` / `SetLabelText()` put text at the middle
  (or start/end) of a line, drawn with a background pad;
  `GetLabelPosition()` / `SetLabelPosition()` control the anchor.  Labels are
  part of the saved regions, and line hit-testing now includes the label boxes,
  so clicking a label selects the edge.
- Route modes are now `straight` / `auto` / `avoid` / `curved` / `orthogonal`
  (`LineShape.SetRouteMode`; legacy `autoRoute = True` means `avoid`).  `auto`
  is straight when clear and curves when blocked, never orthogonal; `avoid`
  does the same but may fall back to an orthogonal L/Z route; `orthogonal` is
  forced.  Curves bow away from the attachment sides using their normals, and
  fall back to the chord normal when sides are unavailable.
- Edge routing: `wxdiagram.routing.route_edge()` (also exported as
  `wxdiagram.route_edge`) and `LineShape.autoRoute` pick a straight segment
  when it is clear, a deflected spline when that dodges unrelated boxes, and an
  orthogonal lane as a last resort.  `autoRoute = "curved"` draws a gentle
  bezier even when the path is clear (the usual UML look); the demo uses a mix
  of straight and curved edges.  Parallel edges between the same two shapes are
  spread into separate lanes.  `False` (default) keeps existing diagrams
  straight.
- `LineShape.SetRouteMode("straight" | "avoid" | "curved" | "orthogonal")` /
  `GetRouteMode()` switch an edge's style at runtime; the demo's right-click
  menu does this per edge and ticks the current style.
- Orthogonal routes leave each shape along its attachment side's normal for a
  10-unit stub (so an edge no longer runs along or inside the box side), then
  take the shortest clear lane just outside the obstacles instead of an
  arbitrary bend multiple.
- Fixed a pen leak: an edge with a label (or a dashed pen) left a transparent
  or dashed pen on the dc, which made later edges invisible or dashed.
- Arrowheads on spline edges use points sampled along the curve (Catmull-Rom)
  for their direction instead of the far-off middle control point, so heads on
  routed curves point along the edge.
- Demo: removed the `utils.py` block that sat over the sample image, dropped
  the Repository box and shortened UserService, and added an EDGE STYLES section
  with coloured boxes connected by straight, curved, auto, avoid and orthogonal
  edges (each labelled; a blocker shows avoidance); the basic shapes are coloured.
- Demo LINES & ARROWS now also shows a spline, a line carrying start/middle/end
  arrow types, and a multi-point bend line.  The left column is roomier: wider,
  better-spaced EDGE STYLES pairs with the lines/arrows column moved right; the
  window stays at its original 1200x760 and zoom-to-fit handles the rest.
- `CompositeShape` is resizable (`Resizeable`): the eight handles scale its
  children proportionally with the frame, and constraints are re-evaluated.
- `PolygonShape.HitTest` uses point-in-polygon, so the interior of a polygon is
  clickable instead of only its outline.
- `EllipseShape.draw()` now sets its own pen/brush: it used to inherit the
  previous shape's brush on the shared dc, so an ellipse's fill changed colour
  depending on draw order (e.g. after clicking another shape changed z-order).
- The scrollable area now starts at the content origin: `getContentOrigin()`
  returns the minimum x/y of the shapes, so content moved or resized into
  negative diagram coordinates stays reachable and is framed by zoom-to-fit
  (previously anything above/left of (0, 0) was outside the scroll range).
- Clicking a resize handle no longer clears the selection/handles, fixing
  disappearing resize indicators.
- Demo uses the sample photograph at `examples/assets/sample-image.jpg`;
  rectangles are resizable and captions are movable.
- `Block.OnRightDown` no longer pops a debug message box (right-click menus are
  application-owned).
- `Shape.marqueeSelectable` so labels and decorations can opt out of marquee
  selection.

### Changed

- Plain drag on empty canvas now draws a marquee; Alt/Space/middle-drag pans.
  Set `emptyDragMode = ShapeCanvas.EMPTY_DRAG_PAN` for the old behaviour.
- `Shape.Copy` no longer uses `copy.deepcopy` (wx fonts/bitmaps are native
  handles and could not be pickled); it copies geometry/regions and shares wx
  objects.
- Wheel scrolling is calibrated to `WHEEL_SCROLL_PIXELS` (20px) per notch and
  accumulates fractional trackpad deltas, so macOS/trackpad scrolling is smooth
  instead of jumping by several lines per event.
- Drag-to-pan ignores the first `PAN_START_THRESHOLD` (3px) of movement, so a
  click with a small hand tremor does not drag the canvas.
- `ShapeCanvas._shapes_bounds()` now delegates to `getContentBounds()` and keeps
  the cache in one place.
- `Shape.Move` docstring clarifies that it takes the shape's centre; use
  `MoveTo` for top-left layout coordinates.

## 0.1.0 — 2026-11-16

First release under the **wxdiagram** name. The library was previously
developed as `ogl2`; that name is retired. The `ogl2` repository remains
available for existing pynsource builds; new work happens here.

### Added

- Zoom and pan on `ShapeCanvas`: `ZoomIn`, `ZoomOut`, `ZoomTo`, `ZoomReset`,
  `ZoomToFit`, `CenterOn`, Ctrl+wheel/pinch zoom, drag-to-pan, and a virtual
  size that tracks the diagram.
- JSON persistence: `Diagram.Save` / `Diagram.Load` and
  `wxdiagram.persistence`, with versioned JSON, nested composites, constraints,
  fonts/colours, line endpoints and arrowheads.
- Stable shape ids: `Shape.SetId` / `GetId` / `AssignNewIds`,
  `Diagram.FindShape(id)`, and stable ids in the JSON format.
- `Shape.Show` / `IsShown` and a working `Diagram.ShowAll`.
- Public spline API: `LineShape.SetSpline` / `IsSpline`.
- Arrow management: `GetArrows`, `AddArrowOrdered`, `ClearArrow`,
  `FindArrowHead(Id)`, `DeleteArrowHead(Id)`, `SetIgnoreOffsets`.
- `CompositeShape.GetConstraints`, `RemoveChildFromConstraints`,
  `DeleteConstraintsInvolvingChild`, and `AddChild(child, addAfter)`.
- `LineShape.GetFrom` / `GetTo`, `Straighten`.
- `DrawArcToEllipse` and clean `GraphicsStraightenLine`, `PolylineHitTest` and
  `RoughlyEqual` helper names.
- `initialize()` replaces `OGLInitialize()`; graphics resources are created
  lazily.
- Test suite and CI, including new regression tests for canvas attachment,
  shape ids, visibility, graphics/arrow accessors and constraint cleanup.

### Changed

- Package renamed `ogl2` → `wxdiagram`; modules renamed `ogl_like` → `core`,
  `oglmisc` → `geometry`.
- `EllipseShapeAndy` → `ConnectableEllipseShape`.
- Removed OGL-specific names from the public API where possible.
- `Diagram.AddShape(..., after=...)` now inserts **after** the reference shape.
- `Diagram.Clear(dc)` now clears the device context, matching classic OGL;
  use `DeleteAllShapes()` to remove shapes.
- Public docs and examples rewritten for the standalone library.

### Fixed

- `ShapeCanvas.SetDiagram` now calls `Diagram.SetCanvas(canvas)`, and
  `Diagram.AddShape` no longer clears an already attached shape canvas.
- `Diagram.GetCanvas()` is populated by normal canvas setup.
- Save/load preserves shape ids.
- `Diagram.ShowAll` is no longer a no-op.
- Removed `CodeBlock` (it called `exec()` on double-click), `ContainerBlock`,
  `CodeFrame`, `AttributeEditor`, `menuMaker`, `rand_bounds`, `get_type` and
  `ConnectableOriginal` from the library.

### Removed from the library

- `pro/` (pynsource `ImageViewer2`)
- pynsource PyInstaller spec, build scripts and macOS icon
- demo-only/app-specific classes listed above

## Prior history

The pre-rename `ogl2` work (zoom/pan, connections, composites, JSON
persistence, demo, tests) is preserved in the `ogl2` repository and its
`standalone` branch. See `PLAN.md` for the migration plan.
