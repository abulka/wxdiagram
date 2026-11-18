# Changelog

See the repository `CHANGELOG.md` for the authoritative history.

## 0.2.4 — 2026-11-18

- Deleting shapes clears their selection handles; `DeleteAllShapes()` and
  `PopShape()` also clear canvas selection chrome.

## 0.2.3 — 2026-11-18

- Group drags no longer move attached edges twice; edges follow their shapes.
- Dragging an attached edge alone no longer detaches it.
- `SetDiagram()` clears the old diagram's selection and handles.

## 0.2.2 — 2026-11-18

- Destination connection ports are round, matching the source dots.
- New layout tutorial covering `ApplyLayout`, routing, options, fixed nodes and
  headless use.
- Expanded layout API reference and a pynsource heritage appendix.
- README and getting-started list all three demos: kitchen sink, shape editor
  and layout playground.

## 0.2.1 — 2026-11-17

- `Shape.MoveTo` for top-left layout coordinates (refreshes attached lines).
- Overridable `ShapeCanvas.getContentBounds()` for zoom-to-fit.
- `getContentOrigin()` for the scroll origin, so negative coordinates stay reachable.
- Documented `autoVirtualSize` / `zoomInputEnabled` opt-outs.
- pynsource integration contract tests.
- Smoother wheel scrolling (20px/notch with fractional trackpad accumulation).
- Drag-to-pan starts after a 3px threshold.

## 0.1.0 — 2026-11-16

- Renamed from `ogl2` to `wxdiagram`.
- New clean repo; removed pynsource build assets and app/demo classes.
- Stable ids, `Diagram.FindShape`, `ShowAll`/`IsShown`, `SetSpline`/`IsSpline`,
  arrow accessors, constraint accessors.
- Fixed canvas attachment, `AddShape(..., addAfter)` ordering, and
  `Diagram.Clear(dc)` semantics.
