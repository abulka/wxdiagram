# wxdiagram

**A zoomable shape-and-connector canvas for wxPython.**

`wxdiagram` gives a wxPython application a modern diagram canvas without the
ceremony of `wx.lib.ogl`: shapes, edges, selection, zoom/pan, and JSON
persistence in a small MIT-licensed package.

It began life as `ogl2`, an internal canvas for
[pynsource](https://github.com/abulka/pynsource). The name is now retired; this
is the standalone library. See `NOTICE.md` for the `wx.lib.ogl` and OGLlike
attribution.

![wxdiagram demo](demo.png)

## Features

- **Canvas with real zoom/pan** — `ZoomIn`, `ZoomOut`, `ZoomTo`, `ZoomReset`,
  `ZoomToFit`, `CenterOn`; Ctrl+wheel and macOS pinch zoom anchored at the
  pointer; drag empty canvas to pan; mouse-wheel scrolling.
- **Selection and handles** — shift-click multi-select, eight resize handles
  (corners + edges; corners proportional by default, Shift = free aspect,
  Alt = from centre), hover ports, drag port-to-shape to connect, an optional
  grid with snap-to-grid, and magnetic alignment guides.
- **Connectors** — attached lines clipped to shape perimeters, arrowheads,
  splines, dashed pens, and bend control points.
- **Shapes** — rectangles, ellipses, polygons, points, lines, bitmaps, divided
  shapes, labelled blocks, composites with constraints, and text labels.
- **JSON persistence** — versioned, portable, no pickle.
- **Keyboard** — Delete, Tab cycle, Ctrl+A, Ctrl+C/V.
- **Headless-friendly** — shapes and the diagram model work without a window.

## Scope

`wxdiagram` is a **canvas library**, not a UML framework or a full layout
engine. It deliberately does not include a UML parser, application menus,
licensing, PlantUML integration, or a Sugiyama/A* layout engine. Layout is
pluggable.

See [Getting started](getting-started.md) and the
[migration guide](migration-from-wx-lib-ogl.md).
