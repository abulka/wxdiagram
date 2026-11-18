# Layout and routing

`wxdiagram` ships a small built-in spring layout and an injectable edge
router. Both are optional: the canvas works with hand-placed shapes and
straight edges, and pynsource keeps its own coordinate mapping and overlap
removal on top.

Positions use **top-left** coordinates, matching `Shape.MoveTo`.

## Running a layout

```python
canvas.ApplyLayout("spring", options={"spacing": 40, "seed": 1})
```

Or launch the playground: `./bin/run-layout` (equivalent to
`uv run python -m wxdiagram.layoutdemo`).

`Diagram.ApplyLayout` works headless (no canvas): it positions nodes and
re-clips attached lines. `ShapeCanvas.ApplyLayout` additionally re-routes
edges, updates the virtual size and refreshes.

Standard options: `spacing` (gap between boxes), `seed` (deterministic
output), `iterations`, `keep_positions` (start from current positions),
`direction` (reserved for layered layouts), `reduce_crossings` (default on)
and `crossing_passes` (refinement sweeps). `LayoutResult.metadata` reports
`crossings_before`, `crossings`, `refinement_moves`, `edge_length_before` and
`edge_length`.

## Edge crossings

Crossings are a **layout** property. The force layout minimises node overlap
and edge length; it does not understand line-line crossings. After the force
pass, `SpringLayout` runs a deterministic local refinement
(`wxdiagram.layout_refine.reduce_crossings`): movable nodes are nudged to
nearby positions when that reduces the number of straight centre-to-centre
edge crossings (or shortens edges without adding crossings). The router then
draws the edges; it avoids boxes, not other edges.

Not every crossing is removable: crossing minimisation is NP-hard, and
non-planar graphs always cross. The refinement is a local improvement, not a
global guarantee. Set `reduce_crossings=False` to compare the raw force
layout. `wxdiagram.layout_metrics.count_crossings` is available if an
application wants to report its own quality numbers.

## Custom layout engine

```python
import wxdiagram

class MyLayout:
    name = "mine"

    def layout(self, nodes, edges, *, options=None, on_step=None):
        # nodes: list[LayoutNode], edges: list[LayoutEdge]
        positions = {node.id: (node.x or 0.0, node.y or 0.0) for node in nodes}
        return wxdiagram.LayoutResult(positions=positions)

wxdiagram.register_layout(MyLayout)
canvas.ApplyLayout("mine")
```

Return top-left positions keyed by node id. `on_step(step, info)` may return
`False` to abort early (progress dialogs, blackboard animation).

## Custom edge router (experimental)

!!! warning "Experimental API"
    Router injection may change or be removed in a minor release. The stable
    surface is `LineShape.SetRouteMode`, `route_edge` and
    `ShapeCanvas.RouteEdges`. The playground does not expose custom routers.

```python
from wxdiagram.routing import BaseRouter, RouteResult

class MidpointRouter(BaseRouter):
    name = "midpoint"

    def route(self, request):
        (x1, y1), (x2, y2) = request.start, request.end
        mid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0 - 25.0)
        return RouteResult(points=(request.start, mid, request.end), style="diagonal")
```

Attach per edge (`line.SetRouter("midpoint")` or an instance) or canvas-wide
(`canvas.SetDefaultRouter("midpoint")`). Override `route_many(requests)` when
the router needs to see all edges at once (lane occupancy, A*).

`request.mode` carries the edge's route mode (`straight`/`auto`/`avoid`/
`curved`/`orthogonal`), `request.obstacles` the foreign rectangles, and
`request.lane_index`/`lane_count` the parallel-edge position.

## Route modes and persistence

`LineShape.SetRouteMode("straight" | "auto" | "avoid" | "curved" |
"orthogonal")` selects the built-in behaviour. The mode is saved in the
diagram JSON (`routeMode`) and restored without forcing a route; files
written before this feature load as `straight`. Experimental router names
are also persisted; unknown names on load fall back to the built-in router.
