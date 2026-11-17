# Changelog

See the repository `CHANGELOG.md` for the authoritative history.

## 0.2.0 — 2026-11-17

- `Shape.MoveTo` for top-left layout coordinates (refreshes attached lines).
- Overridable `ShapeCanvas.getContentBounds()` for zoom-to-fit.
- Documented `autoVirtualSize` / `zoomInputEnabled` opt-outs.
- pynsource integration contract tests.

## 0.1.0 — 2026-11-16

- Renamed from `ogl2` to `wxdiagram`.
- New clean repo; removed pynsource build assets and app/demo classes.
- Stable ids, `Diagram.FindShape`, `ShowAll`/`IsShown`, `SetSpline`/`IsSpline`,
  arrow accessors, constraint accessors.
- Fixed canvas attachment, `AddShape(..., addAfter)` ordering, and
  `Diagram.Clear(dc)` semantics.
