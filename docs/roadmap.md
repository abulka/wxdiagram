# Roadmap

See `PLAN.md` in the repository for the full, maintained plan.

## 0.1 — rename and release

- ✅ New `wxdiagram` repo from the `ogl2` standalone work
- ✅ Rename package/modules, remove app-specific code and OGL vocabulary
- ✅ Stable ids, canvas attachment, `AddShape` ordering, `Clear` semantics
- ✅ Spline/arrow/constraint accessors
- ✅ README, migration guide, docs skeleton
- ✅ Publish 0.1.0 (PyPI, 2026-11-16)
- ✅ Publish 0.2.0 with the pynsource integration hooks
- 🚧 Migrate pynsource and its CI

## 0.2 — interaction and pynsource integration

- 8-way resize handles, proportional resize, marquee selection
- grid and alignment guides
- undo/redo, z-order, duplicate
- buffered/HiDPI-aware painting
- mouse drag tolerance
- ✅ `Shape.MoveTo` for top-left layout coordinates
- ✅ overridable `getContentBounds()` for zoom-to-fit
- ✅ `autoVirtualSize` / `zoomInputEnabled` opt-outs for apps that own scrolling
- ✅ pynsource delegates its viewport (zoom, pinch, pan, virtual size) to this library

## 0.3 — edges

- hybrid curved connectors with obstacle avoidance (from `uml-craft`)
- orthogonal fallback, side selection, lane spreading
- edge labels and markers, edge hit-testing

## 0.4 — layout

- pluggable `Layout` protocol
- simple spring/layered layout
- optional Rust bridge for advanced layout
