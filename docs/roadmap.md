# Roadmap

See `PLAN.md` in the repository for the full, maintained plan.

## 0.1 — rename and release

- ✅ New `wxdiagram` repo from the `ogl2` standalone work
- ✅ Rename package/modules, remove app-specific code and OGL vocabulary
- ✅ Stable ids, canvas attachment, `AddShape` ordering, `Clear` semantics
- ✅ Spline/arrow/constraint accessors
- ✅ README, migration guide, docs skeleton
- ✅ Publish 0.1.0 (PyPI, 2026-11-16)
- ✅ Publish 0.2.1 with the [pynsource](https://github.com/abulka/pynsource) integration hooks
- 🚧 Migrate [pynsource](https://github.com/abulka/pynsource) and its CI

## 0.2 — interaction and pynsource integration

- ✅ 8-way resize handles (corners + edges)
- ✅ proportional resize (Shift = free aspect, Alt = from centre)
- ✅ marquee selection, Shift/Ctrl add, Esc clear, arrow-key nudge
- ✅ grid and alignment guides
- ✅ undo/redo, z-order, duplicate
- ✅ buffered painting (`bufferedPainting`)
- ✅ mouse drag tolerance (3 px)
- ✅ PNG export (`ShapeCanvas.ExportPng`)
- ✅ `Shape.MoveTo` for top-left layout coordinates
- ✅ overridable `getContentBounds()` for zoom-to-fit
- ✅ `getContentOrigin()` so content at negative coordinates stays scrollable
- ✅ `autoVirtualSize` / `zoomInputEnabled` opt-outs for apps that own scrolling
- ✅ [pynsource](https://github.com/abulka/pynsource) delegates its viewport (zoom, pinch, pan, virtual size) to this library

## 0.3 — edges

- ✅ hybrid curved connectors with obstacle avoidance (straight → curved → orthogonal, `route_edge`)
- ✅ orthogonal fallback; ✅ lane spreading for parallel edges; side selection still to do
- ✅ edge hit-testing and labels (middle/start/end)
- ✅ per-edge style switching (`SetRouteMode`, demo/[pynsource](https://github.com/abulka/pynsource) right-click with ticks); `auto` = straight-or-curved, no orth
- markers on curves, label collision avoidance

## 0.4 — layout

- ✅ pluggable `Layout` protocol (`LayoutNode`/`LayoutEdge`/`LayoutResult`, registry)
- ✅ simple spring layout (`SpringLayout`, deterministic seed)
- ✅ experimental router injection (`RouteRequest`/`RouteResult`/`BaseRouter`, per-edge + canvas default, `route_many` batch hook) — UI deliberately not exposed
- ✅ route mode persistence; experimental router-name persistence (backwards compatible)
- ✅ `wxdiagram/layoutdemo.py` playground + `bin/run-layout` (independent of [pynsource](https://github.com/abulka/pynsource))
- ✅ crossing metrics + deterministic post-layout refinement (`reduce_crossings`)
- ✅ `Add random boxes` re-lays out so new nodes participate in the graph
- layered layout (next)
- optional Rust bridge for advanced layout
