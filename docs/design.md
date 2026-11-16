# Design notes

## Geometry

Shapes store their geometry in `x` and `y` lists. For a rectangle those are
the two corners; for a line or polygon they are the control points. `GetX()`
and `GetY()` return the centre. `move()` is relative; `move_to()` moves the
top-left corner.

This is different from `wx.lib.ogl`, which stores a centre and width/height.

## Event model

The canvas hit-tests and dispatches `wx` events to shapes:

- `OnLeftDown(event)`, `OnLeftUp(event)`, `OnLeftDClick(event)`
- `OnRightDown(event)`, `OnRightUp(event)`, `OnRightDClick(event)`
- `OnSelect(event)`, `OnDeselect(event)`, `OnMove(event)`, `OnResize(event)`,
  `OnConnect(event)`

There is no attachment argument and no per-shape begin/drag/end triple.
`wx.lib.ogl` code that overrides `OnLeftClick(x, y, keys, attachment)` needs to
be ported.

## Rendering

Shapes draw directly to a `wx.DC`. `ShapeCanvas` applies `scalex`/`scaley`
with `SetUserScale`. A future release will add a buffered/HiDPI-aware backend.

## Persistence

The JSON format is versioned by `format_version` and carries stable shape ids.
Lines store shape ids, not object references. Composite children are nested.
Colours are names or `#rrggbb[aa]` strings; fonts are face/size/style/weight.
