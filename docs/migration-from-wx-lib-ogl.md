# Migrating from wx.lib.ogl

`wxdiagram` descends from the `wx.lib.ogl` that ships with wxPython. It began
as `ogl2`, a fork of that library created to fix OGL's drag rendering on
modern macOS, and was later renamed and packaged as a standalone canvas.

That shared lineage matters when porting: **most of the working API is the
same**. This page separates four things:

1. why [pynsource](https://github.com/abulka/pynsource) could run the same code against both libraries;
2. the calls that behave identically in both;
3. the small set of differences that need editing;
4. the wx.lib.ogl subsystems `wxdiagram` deliberately does not have.

> **Status (0.2.7):** the compatibility gaps that mattered to [pynsource](https://github.com/abulka/pynsource) —
> canvas attachment, `AddShape(..., addAfter)`, `Diagram.Clear`, `ShowAll`,
> stable ids, spline/arrow/constraint accessors, `CircleShape`, grid/snap,
> line labels and buffered painting — are implemented. What is still missing
> is listed in section 6.

## 1. Why pynsource could use both libraries

### One codebase, two backends

For seven years [pynsource](https://github.com/abulka/pynsource) ran the same GUI modules against `wx.lib.ogl` and
`ogl2`, choosing at import time:

```python
# pynsource, 2019-2026
if PRO_EDITION:
    import ogl2 as ogl
else:
    import wx.lib.ogl as ogl
```

Everything else was written against the `ogl` alias: `UmlCanvas`, the
`DividedShape` subclasses, `LineShapeUml`, `UmlShapeHandler`, the region
formatting, the arrow constants and the diagrams themselves. Switching to
`wxdiagram` was then a one-line change:

```python
import wxdiagram as ogl
```

The reason this worked is not that the libraries are identical. It is that
the classes, method names, constants and data helpers were carried over from
`wx.lib.ogl` on purpose, and [pynsource](https://github.com/abulka/pynsource) used the part of the API that was
stable.

### How much is actually shared?

An automated census of `dir()` output makes `wxdiagram` look like a quarter of
OGL. That number measures the size of the old library's *entire* surface, not
the cost of a port.

A more useful measurement is the API a real application actually calls. At
0.2.7, [pynsource](https://github.com/abulka/pynsource)'s canvas code calls **53 names that OGL defines and that are
present and working in both libraries** — including every shape, line, region,
arrow, canvas, diagram and event-handler call it makes. Only three names it
touched are wx-only (the buffered `Draw()`, the arrow metafile's `Rotate()`,
and one `OnSizingEndDragLeft` base implementation). The eight wxdiagram-only
names it uses (`move_to`, `MoveTo`, route modes, `OnLeftUp`, …) are either new
features or replacements that remove the old workarounds.

Across the compared classes, the OGL-defined API measures (names each module
defines itself, so inherited `wx.Window` members are excluded):

| Measure | Value |
|---|---:|
| OGL-defined names in `wx.lib.ogl` | 304 |
| OGL-defined names in `wxdiagram` | 223 |
| Shared | 166 |
| Shared as a share of wx | **55%** |
| Shared as a share of wxdiagram | **74%** |

`dir()` still undercounts the practical overlap, because it mixes in inherited
`wx.Window` machinery on one side and counts new convenience methods on the
other. `ShapeCanvas`, for example, is 97% shared because most of it is
`wx.ScrolledWindow`.

### The seven real seams

The actual porting work in [pynsource](https://github.com/abulka/pynsource) was this list, not a rewrite:

| Seam | `wx.lib.ogl` | `wxdiagram` | What [pynsource](https://github.com/abulka/pynsource) did |
|---|---|---|---|
| Startup | `OGLInitialize()` | `initialize()` | renamed the call |
| Constructors | `RectangleShape(w, h)` | `RectangleShape(x1, y1, x2, y2)` | adjusted the few shapes it constructs directly |
| Position | centre `SetX`/`SetY` plus a `Move2` monkeypatch | `move_to(left, top)` and `MoveTo(dc, left, top)` | kept one `setpos`/`getpos` helper |
| Fonts | setting the shape font also formatted the region | shape and regions hold fonts separately | added `GetRegions()[0].SetFont(font)` |
| Event handler | `UmlShapeHandler` | `UmlShapeHandlerOglTwo` adapter | swapped the base class and method names |
| Painting | required `canvas.Draw()` to blit its back buffer | paints directly in `EVT_PAINT` | deleted those calls |
| Zoom/pan | application code | built into the canvas | removed the `PRO_EDITION` guards |

There was also a one-off: on modern macOS, `wx.lib.ogl` needed [pynsource](https://github.com/abulka/pynsource)'s
162-line `repair_ogl.py` monkeypatch to draw shapes while dragging.
`wxdiagram` needs no equivalent.

### Why the old library's surface is so much bigger

The missing third is not mostly everyday drawing calls. It is large legacy
subsystems and accessor pairs:

- `DrawnShape` / `PseudoMetaFile` / `DrawOp` — recording drawing operations
  into metafiles, with import and orientation handling;
- `DivisionShape` / `DivisionControlPoint` / `PopupDivisionMenu` — recursive
  subdividable containers;
- the full attachment/branching model (`Attach`, `Detach`, branching styles);
- rotation;
- the old double-buffered canvas (`Draw`, `GetBuffer`);
- many `GetX`/`SetX` pairs for state that `wxdiagram` either exposes directly
  or no longer stores.

A normal diagram application does not use most of that, which is why the same
[pynsource](https://github.com/abulka/pynsource) modules could ignore it on both backends.

## 2. Where the calls are the same

The calls in this section use the same name, arguments and return values in
`wx.lib.ogl` and `wxdiagram` 0.2.7. Where a behaviour detail differs, the note
says so. If your application is built from these, porting is mostly the
import line.

### Canvas and diagram

| Call | Notes |
|---|---|
| `ShapeCanvas(parent)` | same |
| `canvas.SetDiagram(diagram)` | same; it now also attaches shapes and calls `diagram.SetCanvas` |
| `canvas.GetDiagram()` | same |
| `diagram.AddShape(shape, addAfter)` | same; see section 4 for the no-`addAfter` default |
| `diagram.GetShapeList()` | same |
| `diagram.FindShape(id)` | same |
| `diagram.DeleteAllShapes()` | same |
| `diagram.Clear(dc)` | same: clears the device context |
| `diagram.ShowAll(show)` | same |
| `canvas.PrepareDC(dc)` | same |

### Shapes and appearance

| Call | Notes |
|---|---|
| `shape.SetPen(pen)` / `SetBrush(brush)` | same |
| `shape.SetFont(font)` | same one-argument call; wx's optional `regionId` is not supported |
| `shape.SetCanvas(canvas)` / `GetCanvas()` | same |
| `shape.SetDraggable(flag)` / `SetCentreResize(flag)` | same |
| `shape.Show(show)` / `IsShown()` | same |
| `shape.GetX()` / `GetY()` | same: both return the centre |
| `shape.GetBoundingBoxMin()` / `GetBoundingBoxMax()` | same |
| `shape.Move(dc, x, y, display=True)` | same |
| `shape.Delete()` | same |
| `RectangleShape.AddText(string)` | same |
| `RectangleShape.AddRegion(region)` / `GetRegions()` | same |
| `RectangleShape.FormatText(dc, text, index)` | same |
| `DividedShape.SetRegionSizes()` | same |

### Regions and divided shapes

```python
shape = ogl.DividedShape(220, 140)

header = ogl.ShapeRegion()
header.SetText("UserController")
header.SetProportions(0.0, 0.25)
header.SetFormatMode(ogl.FORMAT_CENTRE_HORIZ)
shape.AddRegion(header)

body = ogl.ShapeRegion()
body.SetText("+ get(name)\n+ post(req)")
body.SetProportions(0.0, 0.75)
body.SetFormatMode(ogl.FORMAT_NONE)
shape.AddRegion(body)

shape.SetRegionSizes()
shape.FormatText(dc, body.GetText(), 1)
```

`ShapeRegion`, `ShapeTextLine`, the `FORMAT_*` constants and the region
proportion model are shared, so UML-style class boxes port without changes.

### Lines and arrows

```python
line = ogl.LineShape()
line.SetCanvas(canvas)
line.SetEnds(x1, y1, x2, y2)
line.MakeLineControlPoints(2)
line.SetSpline(True)
line.AddArrow(ogl.ARROW_ARROW, ogl.ARROW_POSITION_END)
line.AddText("uses")
```

| Call | Notes |
|---|---|
| `LineShape.SetEnds(x1, y1, x2, y2)` / `GetEnds()` | same |
| `MakeLineControlPoints(n)` | same |
| `SetSpline(True)` / `IsSpline()` | same |
| `AddArrow(type, end, size, ...)` | same signature |
| `GetArrows()`, `AddArrowOrdered()`, `ClearArrow()` | same |
| `FindArrowHead(id)`, `DeleteArrowHead(id)`, `SetIgnoreOffsets()` | same |
| `LineShape.AddText(string)` | same; labels are drawn in `wxdiagram` |
| `ArrowHead`, `Constraint`, `ConstraintType` | API-identical |

### Event handlers

The base class name and the drawing hooks survive, but handlers in
`wxdiagram` are mixin-style: the shape *is* the handler, so `GetShape()`
returns `self`.

```python
class MyShape(ogl.DividedShape):
    def OnDraw(self, dc):
        super().OnDraw(dc)
        # custom painting, identical in wx.lib.ogl and wxdiagram
```

| Call | Notes |
|---|---|
| subclass `ShapeEvtHandler` | same base class name; see the mixin note above |
| `shape.OnDraw(dc)` / `OnDrawContents(dc)` | same override points |
| `OnSizingEndDragLeft(pt, x, y, keys, attch)` | same signature as the call control points make |
| `GetShape()` | wx returns the associated shape; `wxdiagram` returns `self` because the shape is the handler |

### Constants

`FORMAT_NONE`, `FORMAT_CENTRE_HORIZ`, `FORMAT_CENTRE_VERT`, the `ARROW_*`
family, the `CONSTRAINT_*` family and the `CONTROL_POINT_*` constants use the
same names and values.

## 3. Equivalent calls that did change

These are the calls where the name or argument list differs. This is the
useful table to keep open while porting.

| `wx.lib.ogl` | `wxdiagram` | Notes |
|---|---|---|
| `OGLInitialize()` | `initialize()` | call once before creating shapes |
| `RectangleShape(w, h)` | `RectangleShape(x1, y1, x2, y2)` | `Block` / `ResizableRectangleShape` for handles |
| `EllipseShape(w, h)` | `EllipseShape(x1, y1, x2, y2)` | `ConnectableEllipseShape()` for resizing and ports |
| `CircleShape(diameter)` | `CircleShape(x, y, diameter=...)` | |
| `TextShape(width, height)` | `TextShape(x, y, text, colour, font)` | a caption, not a text box |
| `Shape(canvas)` | `Shape(x=[], y=[])` | |
| `shape.SetX(cx)` / `SetY(cy)` | `shape.move_to(left, top)` / `MoveTo(dc, left, top)` | geometry is stored as x/y point lists |
| `shape.SetSize(w, h)` on a composite | `SetSize(x, y, recursive=False)` | |
| `canvas.InsertShape(shape)` | `canvas.InsertShape(shape, index=0)` | the old call still works |
| `OnLeftClick(x, y, keys, attachment)` | `OnLeftUp(event)` | |
| `OnLeftDoubleClick(x, y, keys, att)` | `OnLeftDClick(event)` | |
| `OnRightClick(x, y, keys, att)` | `OnRightDown(event)` / `OnRightUp(event)` | |
| `OnBeginDragLeft` / `OnDragLeft` | no per-shape equivalent | the canvas moves the shape |
| `OnEndDragLeft(x, y, keys, att)` | `OnEndDragLeft(event)` | no attachment argument |
| `handler.SetShape(shape)` / `GetShape()` | handler is the shape | the shape subclasses `ShapeEvtHandler` |
| `shape.Draw(dc)` | `shape.draw(dc)` | lowercase |
| `ShapeCanvas.FindShape(x, y)` | `canvas.getCurrentShape(event)` | |
| `canvas.Draw()` | — | paints directly in `EVT_PAINT` |
| `repairOGL()` | — | no longer needed |
| `ShapeCanvas(... style=wx.BORDER)` | `ShapeCanvas(... style=0)` | pass `wx.BORDER` explicitly if wanted |

## 4. Same name, different behaviour

A few calls exist in both but do not mean quite the same thing:

- **`Diagram.AddShape(shape)` with no `addAfter`.** `wx.lib.ogl` appends to
  the end of the shape list; `wxdiagram` inserts at the front. Both insert
  after `addAfter` when one is given. The same applies to `canvas.AddShape`,
  which delegates to the diagram. If you rely on insertion order for z-order,
  pass `addAfter` or call `diagram.ChangeShapeOrder(shape, pos)` afterwards.
- **`Shape.SetFont(font)`.** In wx, setting the shape font also drives the
  default region's formatting. In `wxdiagram` the shape and its regions hold
  fonts separately, so set the region font too:
  `shape.GetRegions()[0].SetFont(font)`.
- **`RectangleShape` and `EllipseShape` interactivity.** In wx every `Shape`
  is selectable and resizable. In `wxdiagram` the plain primitives are not;
  use `Block`, `ResizableRectangleShape`, `ConnectableEllipseShape`, or add
  the `Selectable` / `Resizeable` mixins.
- **`TextShape`.** wx's `TextShape(width, height)` is a text box.
  `wxdiagram.TextShape(x, y, text, …)` is a non-interactive caption.
- **Geometry storage.** `GetX()`/`GetY()` still return the centre, but the
  underlying state is `shape.x` / `shape.y` lists of extent points, not
  `_xpos`/`_ypos` plus `_width`/`_height`. Code that pokes those internals
  needs rewriting.
- **`ShapeCanvas` default style.** wx uses `wx.BORDER`; `wxdiagram` uses
  `0`. Pass the style explicitly if your layout depends on it.
- **Event handlers are mixins.** In wx a `ShapeEvtHandler` is a separate
  object associated with a shape. In `wxdiagram` the shape itself inherits
  `ShapeEvtHandler`; `SetShape()` and `SetEventHandler()` are accepted but do
  nothing. Put the handler methods on the shape subclass, and use
  `GetShape()` (which returns `self`) if you want code that reads the same in
  both libraries.
- **Event granularity.** wx distinguishes click from drag with a tolerance
  and passes an `attachment` argument. `wxdiagram` distinguishes down/up,
  ignores motion below `ShapeCanvas.DRAG_TOLERANCE` (3 px, the same value wx
  uses), and has no attachment argument.

## 5. What wxdiagram adds

These are additions, not things inherited from wx:

| Area | wxdiagram |
|---|---|
| **Zoom / pan / fit** | `ZoomIn`, `ZoomOut`, `ZoomTo`, `ZoomReset`, `ZoomToFit`, `CenterOn`, `update_virtual_size`; Ctrl+wheel, macOS pinch, drag-empty-canvas pan |
| **Persistence** | `Diagram.Save(path)` / `Diagram.Load(path)`; versioned JSON with shapes, composites, colours, fonts, arrows and constraints |
| **Connection UX** | hover ports, drag-port-to-shape, `join_shapes`, perimeter-clipped attached edges that re-route when shapes move |
| **Selection / keyboard** | marquee and multi-select, Delete, Tab cycle, Ctrl+A/C/V, undo/redo, nudge, z-order |
| **Grid and guides** | optional grid, snap-to-grid, magnetic alignment guides |
| **Edge labels** | `LineShape.AddText`, `SetLabelPosition`, hit-tested label rectangles |
| **Export** | `ShapeCanvas.ExportPng` at any scale |
| **Layout / routing** | `ApplyLayout("spring")`, crossing reduction, per-edge `SetRouteMode` (`straight`, `auto`, `avoid`, `curved`, `orthogonal`) |
| **Packaging** | explicit imports, `__all__`, uv packaging, tests, CI, demos |

## 6. What wxdiagram still lacks

### Small parity gaps

| Missing | Why it matters |
|---|---|
| Text regions on the base `Shape` | `AddText`, `AddRegion`, `GetRegions`, `FormatText` exist on `RectangleShape`, `DividedShape`, `CompositeShape` and `LineShape`, but not on every shape |
| `ShapeCanvas.FindShape(x, y)` returning `(shape, attachment)` | use `getCurrentShape(event)` instead |
| `GetFont`, `GetTextColour`/`SetTextColour` | font is write-only on some shapes; no text-colour accessor |
| `SetHighlight` / `IsHighlighted` / `Flash` | useful for search results |
| `SetFixedSize`, `SetFixedWidth/Height`, `SetMaintainAspectRatio` | proportional resizing must be done by the application |
| `SetMouseTolerance` | `DRAG_TOLERANCE` is a class attribute; no per-diagram setter |
| `WhollyContains`, `OGLCleanUp` | small helpers |
| `InsertLineControlPoint`, `SetCornerRadius` | line/bend and rounded-rectangle conveniences |
| `SHADOW_*`, `BRANCHING_*`, `OP_*`, `LINE_ALIGNMENT_*` | exported for name compatibility, but shadow and branching behaviour is not implemented |

### Large subsystems

These are deliberate omissions, not accidents:

- **`DrawnShape` / `PseudoMetaFile` / `DrawOp`** — record-and-replay drawing
  and metafile import.
- **`DivisionShape` / `DivisionControlPoint` / `PopupDivisionMenu`** —
  recursive subdividable containers with split/edit menus.
- **Full attachment/branching model** — `Attach`/`Detach`, branching styles,
  attachment ordering, attachment-aware hit-testing. `wxdiagram` uses ports
  and attached lines instead.
- **Rotation** — `SetRotation`, `Rotate`, `GetRotation`.
- **Shadow drawing** — constants exist, no renderer.

If you need one of these, keep the corresponding wx code or open a roadmap
discussion; they are not hiding behind a renamed method.

## 7. Per-class coverage

Public members from `dir()` (including inherited members), at 0.2.7:

| Class | wx members | wxdiagram members | shared | wx coverage |
|---|---:|---:|---:|---:|
| `Shape` | 160 | 73 | 43 | 27% |
| `ShapeEvtHandler` | 34 | 18 | 5 | 15% |
| `RectangleShape` | 166 | 91 | 59 | 36% |
| `EllipseShape` | 164 | 77 | 46 | 28% |
| `PolygonShape` | 173 | 78 | 46 | 27% |
| `TextShape` | 166 | 75 | 44 | 27% |
| `BitmapShape` | 170 | 98 | 65 | 38% |
| `DividedShape` | 168 | 101 | 63 | 38% |
| `LineShape` | 210 | 125 | 79 | 38% |
| `CompositeShape` | 182 | 111 | 74 | 41% |
| `Diagram` | 24 | 22 | 15 | 62% |
| `ArrowHead` | 15 | 15 | 15 | **100%** |
| `Constraint` | 3 | 3 | 3 | **100%** |
| `ShapeCanvas` | 464 | 535 | 449 | **97%** |

Read this table as *surface area*, not *porting effort*. The data and
constraint helpers are identical; the shape hierarchy is smaller because the
metafile, division and attachment subsystems are gone. The calls a typical
application makes are overwhelmingly in the shared 166.

## 8. Porting checklist

1. **Alias the import** and keep the rest of the module:
   ```python
   import wxdiagram as ogl
   ```
2. **Call `initialize()` once** at startup instead of `OGLInitialize()`.
3. **Fix constructors** — rectangles, ellipses, circles and text shapes take
   coordinates rather than width/height:
   ```python
   # before
   shape = ogl.RectangleShape(120, 60)
   # after
   shape = ogl.RectangleShape(0, 0, 120, 60)
   ```
4. **Replace centre-based positioning** with `move_to(left, top)` (diagram
   coordinates) or `MoveTo(dc, left, top)` (inside a paint/refresh pass). Keep
   a single `setpos`/`getpos` helper rather than editing every call site.
5. **Rename the event hooks** you override: `OnLeftClick` → `OnLeftUp`,
   `OnLeftDoubleClick` → `OnLeftDClick`, `OnRightClick` → `OnRightDown`/`Up`.
   Drop the `attachment` argument; keep `OnEndDragLeft(event)`.
6. **Set region fonts explicitly** after `SetFont`.
7. **Delete `canvas.Draw()` and `repairOGL()` calls.** Painting is automatic.
8. **Decide about interaction** — if your shapes were plain
   `RectangleShape`/`EllipseShape` and relied on wx's built-in handles, switch
   to `Block` or add the `Selectable`/`Resizeable` mixins.
9. **Run a contract test.** [pynsource](https://github.com/abulka/pynsource)
   keeps one at `src/tests/test_wxdiagram_contract.py` that asserts every name
   its canvas needs still exists. A twenty-line version of that test will
   catch most upgrade breaks.
10. **Check the omissions list** in section 6 before porting code that uses
    metafiles, divisions, rotation or the attachment model.

The intended positioning is *"inspired by `wx.lib.ogl`, with a modernised
API"* — but the API it kept is the API most applications actually use.
