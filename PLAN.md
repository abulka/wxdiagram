# wxdiagram — single active plan

Status: Phase 0 and Phase 1 done; Phase 2 mostly done. Pynsource migration
and the 0.2+ feature phases remain.
Supersedes: `ogl2/PLAN-2026.md` (keep that file as history; add a
“superseded by `wxdiagram/PLAN.md`” note when we are in build mode).

## Progress log (2026-11-17)

- Pynsource migration started on the `pynsource-1.87` library branch and the
  pynsource `wxdiagram-canvas` branch.
- `0.2.0` adds the integration hooks: `Shape.MoveTo`, overridable
  `getContentBounds()`, and documented `autoVirtualSize` / `zoomInputEnabled`
  opt-outs.
- pynsource now delegates the whole viewport to wxdiagram (zoom, Ctrl+wheel,
  pinch, drag-to-pan, virtual size); its `CanvasResizer` duplicate is deleted.
- Editing pack landed: marquee selection, nudge, duplicate, z-order and
  snapshot undo/redo (with a pynsource graph-aware snapshot provider).
- Resize pack: bitmap resizing keeps float geometry so it tracks the mouse at
  any zoom; handles are positioned when created (no pre-paint hit-test gap);
  eight handles for rectangle-like shapes (corners + edges), edge drags change
  one axis; corner drags clamp instead of inverting; resize is **proportional
  by default with Shift for free aspect**; a resize completes on mouse-up even
  if the pointer has left the handle.
- Scroll area now starts at the content origin: `getContentOrigin()` returns
  the minimum x/y (defaults to all shapes and composite children), so content
  at negative coordinates is scrollable and `ZoomToFit` frames it.  Pynsource
  includes imported images in `getContentBounds()`, fixing unreachable image
  edges after a large resize.
- Decision update: pynsource keeps **one** canvas (`wxdiagram`), removes the
  vendored `src/ogl` and the `ogl2` dependency, and makes the diagram free.
  Pro remains only for ALSM module visualisation. The release stays on `1.x`
  because `rego` keys licences off `int(APP_VERSION)`.

## Progress log (2026-11-16)

- New clean-history repo created from the `ogl2` `standalone` tree.
- `pro/`, pynsource build scripts, PyInstaller spec and macOS icon removed.
- Package/modules renamed: `wxdiagram`, `core`, `geometry`.
- Removed `CodeBlock` (exec), `ContainerBlock`, `CodeFrame`,
  `AttributeEditor`, `menuMaker`, `rand_bounds`, `get_type`,
  `ConnectableOriginal`.
- Stable ids, `Diagram.FindShape`, `ShowAll`/`IsShown`, `SetSpline`/`IsSpline`,
  arrow accessors, `GetConstraints`/constraint cleanup, `GetFrom`/`GetTo`,
  `initialize()`.
- Fixed `SetDiagram`/`AddShape` canvas attachment, `AddShape(..., addAfter)`
  ordering, and `Diagram.Clear(dc)` semantics.
- `uv lock`/`uv sync` updated; 58 tests pass; ruff clean.
- MkDocs site (getting started, cookbook, API, design notes, migration, roadmap).
- `v0.1.0` tagged, GitHub release published, and PyPI upload succeeded on
  2026-11-16: https://pypi.org/project/wxdiagram/
- `uv build` produces `wxdiagram-0.1.0` wheel and sdist.
- `ogl2` is back on `2026-dustoff` and clean; its `standalone` branch is preserved as history.

## 0. Decisions (locked)

| # | Decision | Value |
|---|---|---|
| D1 | Name | `wxdiagram` |
| D2 | Repo | New, clean-history repo `abulka/wxdiagram`; old `ogl2` stays as archive/fallback |
| D3 | Scope | Focused wxPython canvas library: shapes, connectors, zoom/pan, selection, persistence. **Not** a UML framework, not a full layout engine, not an OGL replacement |
| D4 | API names | Keep the current public method names in 0.1 (`draw`, `move`, `getPort`, `SetSize`, etc.). Do a naming pass later only if worth the churn |
| D5 | Package rename | `ogl2` → `wxdiagram`. Update pynsource directly; no public `ogl2` compatibility shim |
| D6 | `ogl2` | Freeze at `2026-dustoff`. No new feature work there |
| D7 | `standalone` work | Copy the `standalone` working tree into `wxdiagram`; do not merge it into `ogl2` |
| D8 | Layout | Pluggable `Layout` protocol. Simple layout in the library; advanced layout stays in `uml-craft`; optional Rust bridge later |
| D9 | First release | `0.1.0` after rename/cleanup/docs; `1.0.0` after the interaction and edge work stabilises |
| D10 | Non-goals | OGL API parity, UML parsing, full Sugiyama/A* engine in Python, web target |

## 1. Scope and positioning

Tagline: **wxdiagram — a zoomable shape-and-connector canvas for wxPython.**

The library owns:

- canvas, view transform, zoom/pan/fit
- shape model and built-in shapes
- selection, handles, drag/resize
- connectors/edges, arrowheads, routing
- diagram persistence (JSON)
- optional pluggable layout

The library does **not** own:

- UML parsing or the pynsource graph model
- application menus, Pro gating, PlantUML/ALSM integration
- pynsource build/CI assets
- advanced layout/routing that belongs in `uml-craft`

## 2. Phase 0 — Fork into a clean repo

Goal: a new repo with clean history and only library code.

1. Create `/Users/andy/Devel/pynsource-project/wxdiagram` from the `standalone`
   working tree (e.g. `git archive standalone | tar -x -C ../wxdiagram`).
2. Do **not** copy `ogl2/.git`; run `git init` and make a clean initial commit.
3. Delete pynsource/app/build material from the new repo:
   - `pro/` (pynsource `ImageViewer2`, no license)
   - `bin/pynsource-github-actions.spec`
   - `bin/buildmac.sh`, `bin/buildwin.bat`, `bin/buildwin_github-actions.iss`
   - `media/pynsource.icns`
   - `ogl2.egg-info/`, caches, `.venv`
4. Keep only library developer helpers in `bin/` (e.g. the demo runner),
   updated to the new package name.
5. Rename `ogl2/` → `wxdiagram/`.
6. Copy `PLAN.md` (this plan) into the repo root.
7. Move the old comparison doc `docs/OGL-VS-OGL2.md` to
   `docs/migration-from-wx-lib-ogl.md`; it is a migration guide, not the identity.

Acceptance:

- `import wxdiagram` works in the new tree.
- No `ogl2`, `pynsource`, `pro/`, `bin/pynsource-*`, or `media/pynsource.*`
  references remain except historical/attribution text.
- Fresh `git log` has one initial commit.

## 3. Phase 1 — Rename and remove app debris

Goal: the package and docs present as a standalone library.

1. `pyproject.toml`:
   - `name = "wxdiagram"`, `version = "0.1.0"`
   - description, keywords, URLs (`abulka/wxdiagram`)
   - `include = ["wxdiagram*"]`
   - keep MIT, `requires-python >=3.10`, `wxpython>=4.2`
2. Rename the module and imports:
   - `import ogl2` → `import wxdiagram`
   - `python -m ogl2.demo` → `python -m wxdiagram.demo`
   - update tests, examples, docs, README, CHANGELOG
3. Remove OGL vocabulary from the public surface:
   - `ogl_like.py` → `core.py` or `shapes.py`
   - `oglmisc.py` → `geometry.py`
   - `OGLInitialize()` → `initialize()` (update pynsource)
   - `OGLRBLF` → private/renamed
   - `OFFLINE_*` helpers → normal public names
   - `EllipseShapeAndy` → `ConnectableEllipseShape`
   - internal `Diagram2`, `ShapeCanvas2`, `LineShape2`, `PolygonShape2` → real
     class names (pynsource does not import these)
4. Delete app/demo debris:
   - `CodeBlock` (contains `exec()` on double-click — security issue)
   - `ContainerBlock` + `CodeFrame`
   - `AttributeEditor`, `menuMaker`, `rand_bounds`, `get_type`
   - `ConnectableOriginal`
   - `ConnectionShape` from the public API; keep a loader-only path if old JSON
     files need it
5. Keep `demo.py` as a safe showcase (no code execution).
6. Move `tests/test_api_contract.py` (pynsource’s import list) to pynsource.
   Add a `wxdiagram` public-API contract test instead.

Acceptance:

- `rg -n "ogl2|OGLInitialize|OGLRBLF|OFFLINE_|EllipseShapeAndy"` is empty
  except historical attribution.
- `python -m wxdiagram.demo` runs.
- `pytest` is green.

## 4. Phase 2 — Correctness before publishing

Fix the P0 items found in the comparison (see the migration doc for detail):

1. `ShapeCanvas.SetDiagram` must call `diagram.SetCanvas(self)`;
   `Diagram2.AddShape` must not overwrite an already attached shape canvas.
2. `Diagram.Clear(dc)` must not silently delete all shapes; either match
   classic OGL (clear the DC) or rename to `DeleteAllShapes`.
3. `Diagram.AddShape(..., addAfter)` must insert **after**, and the keyword name
   must match the base class.
4. `Diagram.ShowAll(show)` either works or is removed.
5. Public `SetSpline` / `IsSpline` (currently only `_isSpline`).
6. Arrow accessors: `GetArrows`, `AddArrowOrdered`, `ClearArrow`,
   `DeleteArrowHead(Id)`, `FindArrowHead(Id)`, `SetIgnoreOffsets`.
7. `CompositeShape.GetConstraints`, `RemoveChildFromConstraints`,
   `DeleteConstraintsInvolvingChild`.
8. Stable shape IDs: `SetId`/`GetId`/`AssignNewIds`, `Diagram.FindShape(id)`,
   and stable IDs in JSON persistence.
9. Export geometry helpers under clean names; add `CircleShape` if cheap.
10. Remove or implement exported-but-unimplemented constants
    (`SHADOW_*`, `BRANCHING_*`, `OP_*`, `LINE_ALIGNMENT_*`).
11. Add `py.typed` only when the public API is actually typed; otherwise omit.

Acceptance:

- Each fix has a regression test.
- `Diagram.GetCanvas()` is correct after `canvas.SetDiagram(...)`.
- `canvas.AddShape(shape)` leaves `shape.GetCanvas() is canvas`.
- Save → load → save produces stable IDs.

## 5. Phase 3 — Docs and 0.1.0

Docs site: `mkdocs-material` + `mkdocstrings` (or Sphinx autodoc if preferred).

Required pages:

- Home / why wxdiagram (screenshot or GIF)
- Getting started (install + 20-line quickstart)
- Concepts: canvas, diagram, shapes, ports/edges, coordinates, zoom
- Cookbook: connect two shapes, custom shape, save/load, zoom to fit, keyboard
- API reference (generated)
- Migration from `wx.lib.ogl` (the renamed comparison doc)
- Design notes: geometry model, event model, rendering, persistence
- Roadmap and non-goals
- Changelog

Also:

- README rewrite; remove “faster than OGL” claims unless benchmarked.
- `AGENTS.md` + `ARCHITECTURE.md` for future sessions.
- `CHANGELOG.md` with the rename and breaking changes.
- `NOTICE.md` keeps wx.lib.ogl / OGLlike attribution.
- Examples gallery with screenshots.
- Headless render test: draw the demo to a `wx.Bitmap`/`MemoryDC`, compare a
  golden PNG.
- Optional benchmark script for paint/zoom/load.

Release 0.1.0:

- `uv build`, inspect wheel/sdist.
- Publish to PyPI; claim the name.
- Tag and GitHub release.

## 6. Phase 4 — Migrate pynsource to wxdiagram

Work on a pynsource branch while `ogl2` stays frozen.

1. `uv pip install -e ../wxdiagram`.
2. Replace `import ogl2 as ogl` with `import wxdiagram as ogl`.
3. Update `from ogl2 import ...` imports.
4. Replace `ogl.OGLInitialize()` with `ogl.initialize()` in
   `pynsource_gui.py` and `test_coords.py`.
5. Remove the `CodeBlock` debug menu/method (or reimplement it in pynsource
   without `exec`).
6. Replace `Move2` monkeypatch with `shape.move_to(...)` and delete `Move2`
   usage if no longer needed.
7. Run pynsource’s full suite (`xvfb-run -a bin/testall` on Linux).
8. Update pynsource CI:
   - `repository: abulka/wxdiagram`
   - checkout path `wxdiagram/`
   - `uv pip install -e wxdiagram/`
   - keep `../ogl2/bin/pynsource-github-actions.spec` until the build assets
     move; then move the spec/icon/scripts to `pynsource/bin` and `pynsource/media`.
9. Update `snap/snapcraft.yaml`, `bin/pip-install-ogl2-alsm-rego`,
   `bin/runpro*`, `bin/build-appimage.sh`, README/BUILDING/AGENTS references.
10. Verify on mac/win/linux CI; then cut pynsource over.

**Pending pynsource moves (from PLAN-2026 §0.2):**

- `ogl2/pro/gui_imageviewer2.py` → `pynsource/src/gui/`; update
  `pynsource_gui.py:65`.
- `ogl2/bin/pynsource-github-actions.spec`, `buildmac.sh`, `buildwin.bat`,
  `media/pynsource.icns` → pynsource; update workflows, spec `pathex`,
  `bin/buildwin.bat`.
- pynsource zoom delegation (`UmlCanvas.zoom_in/out/reset/to_fit`,
  `OnWheelZoom`) → library; delete duplicated zoom code.
- Verify the editable install and full suite after the `__init__` export cleanup.
- History scan before any public release (D10 in the old plan).

Acceptance:

- pynsource Pro opens a sample, zooms, fits, drags/connects, resizes, saves.
- pynsource Community still works on the vendored `src/ogl`.
- CI builds mac/win/linux/snap.

## 7. Phase 5 — 0.2.0 Interaction (pinch from shape-studio)

Source reference: `/Users/andy/Devel/shape-studio/src/ui/canvas.rs`,
`src/shape.rs`, `src/app.rs`.

- ✅ 8 resize handles; ✅ proportional resize by default, Shift = free;
  ✅ Alt = resize from centre.
- ✅ Marquee selection; Shift/Ctrl add; Esc clear; arrow-key nudge.
- ✅ Grid + alignment guides (`Diagram.Snap`/grid API, guide snapping + lines).
- Undo/redo (snapshot or command pattern).
- Z-order: send to back / bring to front; duplicate.
- Stable IDs + `next_id` in the document format.
- ✅ Buffered painting (`bufferedPainting` uses `AutoBufferedPaintDC`); drawing
  stays logical-pixel based and lets wx handle DPI scaling.
- ✅ Mouse drag tolerance (classic OGL uses 3 px).
- ✅ Optional PNG export (`ShapeCanvas.ExportPng`).

Acceptance:

- New interaction tests for handles, marquee, grid, undo/redo.
- Golden render tests still pass.
- No regression in pynsource save/load.

## 8. Phase 6 — 0.3.0 Edges (pinch from uml-craft)

Source reference: `/Users/andy/Devel/uml-craft/app/src/layout/route/curved.rs`
and `layout/route/mod.rs`.

- Hybrid curved connectors:
  - ✅ free bezier when it clears foreign boxes;
  - ✅ deflect control points when that is enough;
  - ✅ fall back to a rounded orthogonal route.
  All in `wxdiagram/routing.py` (`route_edge`), opt-in via
  `LineShape.autoRoute`; `"curved"` draws a free bezier even when clear.
- ✅ lane spreading for parallel edges (automatic in `LineShape.autoRoute`);
  explicit side selection still to do.
- ✅ per-edge route style (`SetRouteMode`/`GetRouteMode`, demo + pynsource
  right-click); curved mode draws a free bezier when clear.
- ✅ Edge hit-testing (segment corridor + label boxes), ✅ labels
  (`AddText`/`SetLabelText`, middle/start/end anchors); markers on curves still
  to do with the router.
- ✅ Basic orthogonal fallback; cascade/A* router later.
- Keep routing independent of layout.

Acceptance:

- Visual fixtures for straight, curved, deflected, rounded.
- Edge hit-testing and label placement tests.
- pynsource UML arrows still render correctly.

## 9. Phase 7 — 0.4.0 Pluggable layout

- Define a `Layout` protocol: nodes (id, size, optional fixed position) and
  edges (source, target, kind) in; positions out.
- Ship a simple spring and/or layered layout in Python.
- Keep advanced Sugiyama/Brandes–Köpf/A* in `uml-craft`.
- If advanced layout is needed in pynsource, evaluate:
  1. pure-Python port (maintainable, slow to build);
  2. PyO3 wheel from a `umlcraft-layout` crate (best UX, build matrix);
  3. subprocess/JSON bridge (easiest, distribution-heavy).
- Do not block 1.0 on this phase.

Acceptance:

- `layout=` is optional; the library works with no layout engine.
- A small graph lays out deterministically.

## 10. Phase 8 — Archive ogl2

- Put a “frozen / superseded by wxdiagram” note in `ogl2/README.md` and
  `PLAN-2026.md`.
- Keep `2026-dustoff` available for old pynsource builds.
- Archive the repo once pynsource CI no longer checks it out.
- Remove mirrored `oglmisc.py` maintenance once the Community canvas decision
  is made.

## 11. Code move inventory

### Move to pynsource

- `pro/gui_imageviewer2.py`
- `bin/pynsource-github-actions.spec`
- `bin/buildmac.sh`, `bin/buildwin.bat`
- `media/pynsource.icns`
- pynsource-specific tests/contracts

### Delete from the library

- `CodeBlock`, `ContainerBlock`, `CodeFrame`, `AttributeEditor`
- `menuMaker`, `rand_bounds`, `get_type`
- `ConnectableOriginal`
- `pro/`, pynsource build assets, pynsource icon

### Keep in the library

- `Shape`, `ShapeCanvas`, `Diagram`, standard shapes, `DividedShape`,
  `CompositeShape`, `Constraint`, `ShapeRegion`, `ShapeTextLine`, `geometry`,
  `persistence`
- interaction handles (`Node`/`INode`/`ONode`/`ResizeableNode`) as internal
  modules, not public API
- demo, examples, tests, docs

### Stays in pynsource

- `UmlShapeHandlerOglTwo`, `uml_shapes.py`, `uml_lines.py`,
  `uml_canvas.py`, `canvas_resizer.py`, `coord_utils.py`
- Pro gating, menus, PlantUML/ALSM, build assets
- vendored `src/ogl/` (Community) until a deliberate migration

## 12. Verification checklist

- [ ] New repo has clean history and only library code.
- [ ] `rg "ogl2|OGLInitialize|OGLRBLF|OFFLINE_|EllipseShapeAndy"` clean.
- [ ] `pytest` green (ported + new tests).
- [ ] `python -m wxdiagram.demo` runs.
- [ ] `uv build` produces a clean wheel/sdist.
- [ ] 0.1.0 published.
- [ ] pynsource branch passes full suite with `wxdiagram`.
- [ ] pynsource CI builds mac/win/linux/snap.
- [ ] `ogl2` frozen and documented as superseded.
- [ ] Docs build; screenshots generated.
- [ ] Benchmark recorded (if “faster” is claimed).

## 13. Risks

- **Breaking pynsource CI while moving build assets.** Move the spec/icon into
  pynsource first, verify CI, then switch the dependency. Keep `ogl2` as a
  fallback.
- **Two libraries diverging.** Freeze `ogl2`; all new work only in `wxdiagram`.
- **Method renaming churn.** Not doing it in 0.1; revisit in 0.2 with a
  coordinated pynsource update.
- **Rust layout port scope.** Keep it out of 1.0; use a bridge only if needed.
- **Community canvas duplication.** Decide later whether Community migrates to
  `wxdiagram` or `src/ogl` is frozen.
- **History/licensing.** Clean repo avoids leaking pynsource-derived code;
  keep attribution in `NOTICE.md`.
- **“Faster” claim.** Benchmark before repeating it.
- **Security.** No `exec()` in library code.

## 14. Open decisions (later)

- Whether pynsource Community eventually uses `wxdiagram`.
- Whether advanced layout arrives via pure Python, PyO3, or subprocess.
- Whether to add a `GraphicsContext` renderer for antialiasing/rotation/shadows.
- The long-term split between pynsource and `uml-craft`.
