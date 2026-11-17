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

### Changed

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
