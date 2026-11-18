# wxdiagram

**A zoomable shape-and-connector canvas for wxPython.**

[![PyPI](https://img.shields.io/pypi/v/wxdiagram.svg)](https://pypi.org/project/wxdiagram/)

`wxdiagram` gives a wxPython application a modern diagram canvas without the
ceremony of `wx.lib.ogl`: shapes, edges, selection, zoom/pan, and JSON
persistence in a small MIT-licensed package.

It began life as `ogl2`, an internal canvas for
[pynsource](https://github.com/abulka/pynsource). The name is now retired; this
repository is the standalone library. See `NOTICE.md` for the `wx.lib.ogl` and
OGLlike attribution.

![wxdiagram demo](https://raw.githubusercontent.com/abulka/wxdiagram/main/docs/demo.png)

[![Docs](https://img.shields.io/badge/docs-abulka.github.io%2Fwxdiagram-blue)](https://abulka.github.io/wxdiagram/)

## Documentation

- [Getting started](https://abulka.github.io/wxdiagram/getting-started/)
- [Tutorials](https://abulka.github.io/wxdiagram/tutorials/canvas-and-shapes/):
  [canvas and shapes](https://abulka.github.io/wxdiagram/tutorials/canvas-and-shapes/),
  [edges, labels and arrows](https://abulka.github.io/wxdiagram/tutorials/edges-and-labels/),
  [images, composites and export](https://abulka.github.io/wxdiagram/tutorials/images-composites-export/)
- [Cookbook](https://abulka.github.io/wxdiagram/cookbook/)
- [API reference](https://abulka.github.io/wxdiagram/api/)
- [Migration from wx.lib.ogl](https://abulka.github.io/wxdiagram/migration-from-wx-lib-ogl/)

## Features

- **Canvas with real zoom/pan**: `ZoomIn`, `ZoomOut`, `ZoomTo`, `ZoomReset`,
  `ZoomToFit`, `CenterOn`; Ctrl+wheel and macOS pinch zoom anchored at the
  pointer; drag empty canvas to pan; mouse-wheel scrolling; virtual size tracks
  the diagram so panning cannot wander into empty space.
- **Selection and editing**: marquee select (plain drag on empty canvas),
  Shift/Ctrl add, Esc clear, arrow-key nudge, duplicate, z-order, undo/redo,
  corner resize handles (proportional by default, Shift = free aspect,
  Alt = from centre), and drag from a side dot onto another shape to connect.
  Non-connectable shapes also get edge handles.
- **Grid and guides**: optional background grid, snap-to-grid and magnetic
  alignment guides to other shapes' edges and centres.
- **Connectors**: attached lines whose endpoints are clipped to the shapes'
  perimeters, so edges always meet the facing sides and re-route when shapes
  move. Explicit lines support arrowheads (start/middle/end), splines, dashed
  pens, bend control points, editable labels and per-edge routing modes
  (`straight`, `auto`, `avoid`, `curved`, `orthogonal`).
- **Shapes**: resizable rectangles, ellipses, polygons (interior hit-testing),
  points, lines, resizable bitmaps, divided (UML-style) shapes, labelled
  blocks, composite shapes with layout constraints that scale their children,
  non-interactive text labels and movable text captions.
- **Layout and routing hooks**: an optional spring layout
  (`ShapeCanvas.ApplyLayout`), crossing-aware refinement, and experimental
  injectable edge routers (`LineShape.SetRouter`,
  `ShapeCanvas.SetDefaultRouter`, batch `route_many`).
- **Export**: render the diagram to PNG at any scale (`ShapeCanvas.ExportPng`).
- **JSON persistence**: `Diagram.Save(path)` / `Diagram.Load(path)` or
  `wxdiagram.persistence`; versioned, portable, no pickle.
- **Keyboard**: Delete, Tab cycle, Ctrl+A, Ctrl+C/V.
- **Headless-friendly**: shapes and the diagram model work without showing a
  window.

## Installation

Requires Python 3.10+ and wxPython 4.2+.

```bash
pip install wxdiagram
```

On PyPI: <https://pypi.org/project/wxdiagram/>

or from source with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/abulka/wxdiagram.git
cd wxdiagram
uv sync
```

## Quickstart

```python
import wx
import wxdiagram

app = wx.App(redirect=False)
frame = wx.Frame(None, title="wxdiagram minimal", size=(600, 400))

canvas = wxdiagram.ShapeCanvas(frame)
canvas.SetDiagram(wxdiagram.Diagram())

shape = wxdiagram.RectangleShape(100, 100, 300, 200)
shape.AddText("hello world")
canvas.InsertShape(shape, 999)

frame.Show()
canvas.update_virtual_size()
app.MainLoop()
```

Connect two blocks with an attached line:

```python
canvas.join_shapes(left_block, right_block)
```

The edge routes through the box perimeters, so it stays correct from any
direction and follows the shapes when they move.

## Demos and examples

There are three demos:

```bash
# 1. Kitchen sink: the full canvas API.
uv run python -m wxdiagram.demo

# 2. Shape editor: Shape Studio-style properties panel and tools.
uv run python -m wxdiagram.shapesdemo

# 3. Layout playground: spring layout, sizes and routing modes.
uv run python -m wxdiagram.layoutdemo
```

The same entry points are wrapped by `./bin/run`, `./bin/run-shapes` and
`./bin/run-layout`.

The kitchen-sink demo is a tour of UML-style class boxes, a composite, a
basic-shape gallery, bitmaps, captions, a polyline and an arrowed line. The
File/Edit/Add/Arrange/View menus expose JSON save/load, undo/redo, duplicate,
delete, z-order, image import and zoom.

The shape editor adds rectangles, circles, ellipses, triangles and free lines;
edit name, position, size, colours and border width in the resizable, wrapping
properties panel on the right; connect shapes by dragging a round side dot onto
another shape; group/ungroup, duplicate and reorder.
File/Edit/Add/Arrange/View/Help menus and right-click menus match the main
demo, and View > Theme switches between System, Light and Dark.

The layout playground builds a small graph, runs the spring layout, and lets you
switch route modes, randomise sizes and reset the graph. (Router injection is
experimental and is not exposed in the playground.)

See the [layout tutorial](docs/tutorials/layout-and-routing.md) for using
`ApplyLayout` and `RouteEdges` in your own app.

Small runnable scripts live in `examples/`:

- `minimal_canvas.py` — the 30-line hello world
- `connect_two_blocks.py` — attached-line connections
- `zoom_to_fit.py` — zoom and pan
- `save_load.py` — save and load with JSON

## Scope

`wxdiagram` is a **canvas library**, not a UML framework or a full layout
engine. It deliberately does not include:

- a UML parser or graph model
- application menus, licensing, or PlantUML integration
- a Sugiyama/A* layout engine
- complete `wx.lib.ogl` API parity

Layout is pluggable; an application can run its own layout and hand positions
to the canvas. See `docs/migration-from-wx-lib-ogl.md` for a detailed
comparison with `wx.lib.ogl`.

## Status

Beta (`0.2.3`). The public API is still settling, so pin a version if you
depend on it. pynsource is the main downstream consumer.

## License

MIT, see `LICENSE.md`. The `wx.lib.ogl` and OGLlike attribution is in
`NOTICE.md`.
