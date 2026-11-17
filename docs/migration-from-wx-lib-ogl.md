This page compares `wxdiagram` with the `wx.lib.ogl` that ships with
wxPython 4.3.2. It is a migration guide, not a compatibility promise: the two
libraries share a lineage and some class names, but `wxdiagram` is a focused
canvas library with a different API.

> **Status (0.1.0):** the P0 items in section 2 — canvas attachment,
> `AddShape(..., addAfter)` ordering, `Diagram.Clear`, `ShowAll`, stable ids,
> and the spline/arrow/constraint accessors — are fixed. The API differences
> in section 3 still apply.

## Bottom line

`wxdiagram` is **a fork/reimplementation, not a superset or drop-in
replacement** for `wx.lib.ogl`. It adds genuinely useful new capabilities
(zoom/pan, JSON persistence, connection UX, keyboard editing), but it also
exposes only about **a quarter to a third of the per-shape API** of
`wx.lib.ogl`, with different constructors, a different geometry model, and a
different event model.

The intended positioning is: *“inspired by `wx.lib.ogl`, with a modernised
API”* — not *“`wx.lib.ogl` plus extras”*.

---

## 1. What wxdiagram adds that wx.lib.ogl does not have

These are real additions, not things inherited from wx:

| Area | wxdiagram | wx.lib.ogl |
|---|---|---|
| **Zoom / pan / fit** | `ZoomIn`, `ZoomOut`, `ZoomTo`, `ZoomReset`, `ZoomToFit`, `CenterOn`, `update_virtual_size`; mouse/selection/centre anchors; Ctrl+wheel, macOS pinch, drag-empty-canvas pan; configurable `ZOOM_MIN_SCALE`, `ZOOM_MAX_SCALE`, `ZOOM_STEP` | **Nothing.** wx only gives you a `ScrolledWindow`; the app must implement zoom entirely |
| **Persistence** | `Diagram.Save(path)` / `Diagram.Load(path)` and `wxdiagram.persistence`: versioned JSON, shape registry, nested composites/containers, colours/fonts, line endpoints, arrowheads, constraints | **Nothing** in current wx. (No `SaveFile`/`LoadFile` either) |
| **Connection UX** | Hover a shape to reveal ports; drag port→shape to connect; `join_shapes`; finished edges are attached lines clipped to shape perimeters and re-route when shapes move | Has an attachment model, but no hover ports, no `join_shapes`, no perimeter-clipped "attached line" convenience |
| **Selection / keyboard** | Canvas-owned `selectedShapes`, shift-click multi-select, Delete, Tab cycle, Ctrl+A, Ctrl+C/V, resize handles | No selection manager and no key bindings; each application does it |
| **Non-interactive text labels** | `TextShape(x, y, text, colour=…)`, never hit-tested, saves/loads with the diagram | `TextShape` exists but is a full text shape; no “caption/label that never gets in the way” |
| **Shape set** | `Block`, `PointShape`, `LinesShape`, `ConnectionShape`, `ConnectableEllipseShape`; mixins `Connectable`, `Resizeable`, `Selectable`, `Attributable` | A different, deeper hierarchy (`Shape` has selection/resizing/attachment built in) |
| **UML helpers** | `DividedShape.AddAttribute/AddAttributes/RemoveAttribute`, `SetLabelColour`, region proportions + `FORMAT_*` layout | `DividedShape` has divisions and control points, but no attribute helpers |
| **Composite persistence** | Serializable children + constraints, `Constrain()`, `FindConstraint`, `DeleteConstraint`, `RemoveChild` | `CompositeShape` and constraints exist (richer in divisions), but no save/load |
| **Geometry convenience** | `move_to`, `move_center`, `Copy`, `ChangeShapeOrder`, `AppendShape`, `PopShape`, `line_control_points_to_xy_points` | `Move`/`SetX`/`SetY` only |
| **Robustness / packaging** | Canvas auto-attachment for insertion paths, lazy pens/fonts, `int()` casts for Python 3.10+, `ast.literal_eval` instead of `eval`, explicit imports + `__all__`, uv packaging, demo, examples, 50 tests, CI | Older code, no packaging/tests/demo |

**Caveat on lineage:** arrowheads, splines, composites and divided shapes
already existed in `wx.lib.ogl`. wxdiagram's arrow code is a port; splines now
have a public API; composites and divided shapes are reimplemented with JSON
persistence.

---

## 2. What wx.lib.ogl has that wxdiagram does not

### Fixed in 0.1

- `ShapeCanvas.SetDiagram` connects the diagram and attaches shapes.
- `Diagram.AddShape(..., addAfter)` inserts after the reference shape.
- `Diagram.Clear(dc)` clears the DC; `DeleteAllShapes()` removes shapes.
- `Diagram.ShowAll(show)` and `Shape.Show`/`IsShown` work.
- Stable shape ids, `Diagram.FindShape(id)`, stable ids in JSON.
- Public `SetSpline`/`IsSpline`.
- Arrow accessors (`GetArrows`, `AddArrowOrdered`, `ClearArrow`,
  `FindArrowHead(Id)`, `DeleteArrowHead(Id)`, `SetIgnoreOffsets`).
- `CompositeShape.GetConstraints` and constraint cleanup helpers.
- Clean `GraphicsStraightenLine`, `PolylineHitTest`, `RoughlyEqual`,
  `DrawArcToEllipse` names.

### Remaining P0

| Missing in wxdiagram | Why it matters |
|---|---|
| **Mouse drag tolerance** (`DEFAULT_MOUSE_TOLERANCE`, `Diagram.SetMouseTolerance`, `GetMouseTolerance`, canvas tolerance logic) | wx ignores drags within 3 px; wxdiagram starts moving on the first 1 px motion. Noticeable click/drag feel difference. |
| **`CircleShape`** | Trivial convenience over `EllipseShape`; wx has it. |
| **`WhollyContains`, `OGLCleanUp`** | Small helper parity; not critical. |
| **Unimplemented exported constants** | `SHADOW_*`, `BRANCHING_*`, `OP_*`, `LINE_ALIGNMENT_*` are exported but shadow/branching/sensitivity are not implemented. Either implement or stop exporting them (especially `SHADOW_*`). |

### P1 — usability parity (worth adding)

- **Grid + snap**: `Diagram.Snap(x, y)`, `SetGridSpacing`, `GetGridSpacing`, `SetSnapToGrid`, `GetSnapToGrid`, `ShapeCanvas.Snap`. Completely absent in wxdiagram.
- **Off-screen buffer / double-buffered painting**: wx's `ShapeCanvas.Draw()`, `GetBuffer()`, `OnSize()`, `BG_STYLE_PAINT`. wxdiagram paints directly in `onPaintEvent`, so large diagrams may flicker/repaint more. Worth benchmarking against your “faster” claim.
- **Line labels**: wx's `LabelShape`, `LineShape.AddText`, `FormatText`, `GetRegions`, `GetLabelPosition`, and label hit-testing. wxdiagram creates three label regions in `LineShape` but never draws them (`_labelObjects` stays `None`), so edge labels are effectively unsupported.
- **Text regions on the base `Shape`**: `AddText`, `AddRegion`, `GetRegions`, `FindRegion`, `NameRegions`, `SetRegionName`, `FormatText`, `GetFormatMode`, `SetFormatMode`. Today these exist only on some subclasses.
- **8-way resize handles**: ✅ wx's `MakeControlPoints` gives 8 handles (corners + edges); wxdiagram does the same for rectangle-like shapes (`RECT_HANDLES`). Corner drags are proportional by default (Shift = free); edge drags resize one axis. Other resizable shapes still get one `ResizeableNode` per x/y point, and a plain `RectangleShape` (not `Selectable`/`Resizeable`) still has no handles.
- **Fixed size / maintain aspect ratio**: `SetFixedSize`, `SetFixedWidth/Height`, `SetMaintainAspectRatio` (used by `CircleShape` in wx).
- **Highlight / flash**: `SetHighlight`, `IsHighlighted`, `Flash` (useful for search results or selection feedback).
- **Base-shape accessors**: `GetFont/SetFont`, `GetTextColour/SetTextColour`, `GetPen/GetBrush`, `GetDrawHandles/SetDrawHandles`, `Draggable`, `SetSensitivityFilter`.
- **`ShapeCanvas.FindShape(x, y)`** returning `(shape, attachment)`; `Shape.Draw`/`DrawContents` naming aliases.

### P2 — large subsystems; decide deliberately

- **`DrawnShape` / `PseudoMetaFile` / `DrawOp` family** — draw-a-shape-like-a-DC recording plus metafile import and 4 orientations. You already dropped this; keep it on the roadmap.
- **`DivisionShape` / `DivisionControlPoint` / `PopupDivisionMenu`** — recursive subdividable containers with right-click split/edit menus. wxdiagram has no recursive-container equivalent; this is the biggest shape-editing feature wx has that wxdiagram lacks.
- **Full attachment/branching model** — `Attach`/`Detach`, branching styles (`BRANCHING_ATTACHMENT_NORMAL/BLOB`), attachment ordering, `MoveLineToNewAttachment`, attachment-aware hit-testing. wxdiagram deliberately simplified connections; only port this if you need orthogonal routing/hierarchies.
- **Rotation** (`SetRotation`, `Rotate`, `GetRotation`) — absent; hard to do well with plain `wx.DC`, likely needs `GraphicsContext`.
- **Shadow drawing** — constants exist, no implementation.
- **Quick edit mode** — minor; wx uses it to suppress refreshes/handles.

---

## 3. API comparison

### 3.1 Namespace

**Common classes (19):** `Shape`, `ShapeEvtHandler`, `RectangleShape`, `EllipseShape`, `PolygonShape`, `TextShape`, `BitmapShape`, `DividedShape`, `LineShape`, `ControlPoint`, `LineControlPoint`, `ArrowHead`, `ShapeCanvas`, `Diagram`, `CompositeShape`, `Constraint`, `ConstraintType`, `ShapeRegion`, `ShapeTextLine`.

**In wx, absent from wxdiagram (15):** `CircleShape`, `DrawnShape`, `DrawOp`, `OpDraw`, `OpPolyDraw`, `OpSetClipboard`/`OpSetClipping`, `OpSetGDI`, `PseudoMetaFile`, `DivisionShape`, `DivisionControlPoint`, `DividedShapeControlPoint`, `PolygonControlPoint`, `PopupDivisionMenu`, `LabelShape`, `OGLConstraint`.

**In wxdiagram, absent from wx:** `Block`, `PointShape`, `LinesShape`, `ConnectionShape`, `ConnectableEllipseShape`, `Attributable`, `Connectable`, `Selectable`, `Resizeable`.

### 3.2 Per-class API coverage

Counts are public members from `dir()` (so they include inherited members). This is the clearest measure of “how much of the old API is still there”:

| Class | wx members | wxdiagram members | shared | wx coverage |
|---|---:|---:|---:|---:|
| `Shape` | 160 | 51 | 35 | **22%** |
| `ShapeEvtHandler` | 34 | 18 | 5 | 15% |
| `RectangleShape` | 166 | 72 | 55 | **33%** |
| `EllipseShape` | 164 | 54 | 38 | 23% |
| `PolygonShape` | 173 | 54 | 38 | 22% |
| `TextShape` | 166 | 53 | 36 | 22% |
| `BitmapShape` | 170 | 78 | 61 | **36%** |
| `DividedShape` | 168 | 81 | 59 | 35% |
| `LineShape` | 210 | 73 | 56 | 27% |
| `CompositeShape` | 182 | 88 | 67 | 37% |
| `Diagram` | 24 | 15 | 9 | 38% |
| `ArrowHead` | 15 | 15 | 15 | 100% |
| `Constraint` | 3 | 3 | 3 | 100% |

So the **data/constraint helper classes are API-identical**, but the **shape hierarchy is substantially reduced**.

### 3.3 Constructors and semantics differ

These are the traps most likely to bite someone porting from `wx.lib.ogl`:

| API | wx.lib.ogl | wxdiagram |
|---|---|---|
| `Shape` | `Shape(canvas=None)` | `Shape(x=[], y=[])` |
| `RectangleShape` | `RectangleShape(w=0, h=0)` | `RectangleShape(x=20, y=20, x2=90, y2=90)` |
| `EllipseShape` | `EllipseShape(w, h)` | `EllipseShape(x, y, x2, y2)` |
| `TextShape` | `TextShape(width, height)` — a full text shape | `TextShape(x, y, text, colour, font)` — a caption |
| Geometry storage | centre `_xpos/_ypos` + `_width/_height` | `x`/`y` **lists** of points; `_xpos/_ypos` are computed properties; `_width` asserts exactly 2 x-points |
| `InsertShape` | `InsertShape(object)` | `InsertShape(shape, index=0)` |
| `AddShape` | inserts **after** `addAfter` | inserts **after** `addAfter` |
| `Diagram.Clear(dc)` | clears the DC | deletes all shapes and deselects |
| `Diagram.ShowAll(show)` | calls `Show` on every shape | no-op |
| `RectangleShape` interactivity | selectable/resizable/connectable via base `Shape` | **not** `Selectable`/`Resizeable`; use `Block` for that |
| `EllipseShape` | resizable | no `SetSize`; use `ConnectableEllipseShape` |
| `CompositeShape.SetSize` | `(w, h, recursive=True)` | inherited `(x, y, recursive=False)` |
| `ShapeCanvas.SetDiagram` | only stores the diagram | also attaches shapes, but does **not** call `diagram.SetCanvas(self)` |
| `ShapeCanvas` default style | `wx.BORDER` | `0` |

### 3.4 Event model

This is the biggest incompatibility for application code:

| wx.lib.ogl | wxdiagram |
|---|---|
| `OnLeftClick(x, y, keys, attachment)` | `OnLeftDown(event)` / `OnLeftUp(event)` |
| `OnLeftDoubleClick(x, y, keys, attachment)` | `OnLeftDClick(event)` |
| `OnRightClick(x, y, keys, attachment)` | `OnRightDown(event)` / `OnRightUp(event)` / `OnRightDClick(event)` |
| `OnBeginDragLeft(x, y, keys, attachment)` | no per-shape begin-drag callback |
| `OnDragLeft(draw, x, y, keys, attachment)` | no per-shape drag callback; canvas calls `shape.move(dx, dy)` directly |
| `OnEndDragLeft(x, y, keys, attachment)` | `OnEndDragLeft(event)` (broadcast, no attachment) |
| `OnBeginDragRight` / `OnDragRight` / `OnEndDragRight` | absent |
| Canvas hooks `OnLeftClick`, `OnBeginDragLeft`, `OnDragLeft`, `OnEndDragLeft`, `OnMouseEvent` | Canvas hooks `OnLeftDown`, `OnLeftUp`, `OnMotion`, `OnMouseWheel`, `OnMagnify`, `OnKeyDown` |

Consequences:
- wx-style overrides silently do nothing (different method names or signatures).
- There is no `attachment` argument, so attachment-aware code has to be redesigned.
- wxdiagram distinguishes down/up; wx distinguishes click/drag with tolerance.
- wxdiagram adds shape-level `OnSelect`, `OnDeselect`, `OnMove`, `OnResize`, `OnConnect` — useful, but new.

### 3.5 Naming and API hygiene

- wxdiagram mixes two conventions: `SetPen`, `AddText`, `HitTest`, `Select`, `ZoomToFit`, `update_virtual_size`, `join_shapes`, `select`, `deselect`, `draw`, `move`, `move_to`. There is no consistent rule.
- Some public names still reflect implementation history: `sanity()`,
  `onPaintEvent`, and a mix of CamelCase/snake_case methods.
- `wxdiagram.__init__` also leaks `version` and `PackageNotFoundError` from `importlib.metadata` (not in `__all__`, but importable).
- wx's docs are a complete API reference; wxdiagram's `docs/source` is still a Sphinx stub, so users have only the README.

---

## Migration guidance

1. **Don't treat wxdiagram as a drop-in `wx.lib.ogl` replacement.** Use this table when porting code: constructors, `Draw`→`draw`, event signatures and the geometry model all differ.
2. **Fix the P0 items before 1.0.** The `AddShape`/`SetDiagram` canvas-detachment bug, `Diagram.Clear` semantics, `AddShape(after)` order, missing `SetSpline`, missing `GetConstraints`, and unimplemented exported constants are all release-blocking for a general-purpose library.
3. **Add P1 selectively** — grid/snap, drag tolerance, buffered painting, line labels, and 8-way resize are the highest-value parity items. Rotation, divisions, drawn shapes, and branching attachments should be explicit roadmap decisions, not accidental omissions.
4. **Keep the naming policy consistent.** The package/class renames are done;
   the remaining mixed CamelCase/snake_case methods are a 0.2 cleanup. Add a
   `wxdiagram.compat` shim only if users need wx-style aliases.
5. **Publish real API docs** and add a compatibility contract test for the wx-inspired names you decide to support.

If you want, I can turn the P0/P1 list into a concrete ordered implementation plan (with file-level changes and test additions) once you switch out of Plan mode.

