# Changelog

## 0.2.0 — 2026-11-17

The pynsource integration release. Adds the small number of hooks the
pynsource canvas needs, without pulling any application code into the library.

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
