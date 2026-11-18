# Tutorial 4 — Layout and routing

`wxdiagram` keeps layout and routing separate.  A layout engine decides where
each shape's top-left corner goes; the edge router then draws the attached
lines between them.  Both are optional: you can hand-place shapes and leave
edges straight.

## Lay out a canvas

```python
import wx

import wxdiagram


class Frame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wxdiagram tutorial 4", size=(900, 620))
        self.canvas = wxdiagram.ShapeCanvas(self)
        self.canvas.SetDiagram(wxdiagram.Diagram())

        client = wxdiagram.Block()
        client.label = "Client"
        client.x = [40, 200]
        client.y = [40, 120]

        service = wxdiagram.Block()
        service.label = "Service"
        service.x = [260, 460]
        service.y = [60, 150]

        store = wxdiagram.Block()
        store.label = "Store"
        store.x = [500, 680]
        store.y = [40, 130]

        for shape in (client, service, store):
            self.canvas.InsertShape(shape, 999)

        self.canvas.join_shapes(client, service)
        self.canvas.join_shapes(service, store)

        result = self.canvas.ApplyLayout(
            "spring",
            options={"spacing": 50, "seed": 7},
        )
        print(result.metadata["crossings"])

        self.canvas.update_virtual_size()
        self.canvas.ZoomToFit()
        self.Show()


app = wx.App(redirect=False)
Frame()
app.MainLoop()
```

`ShapeCanvas.ApplyLayout` does three things:

1. collects the top-level, non-line shapes and their attached edges;
2. runs the layout engine and moves each shape to its **top-left** position;
3. re-routes every edge, updates the scroll extent and refreshes.

`Diagram.ApplyLayout` is the headless equivalent.  It positions shapes and
re-clips attached lines, but it has no canvas to re-route or refresh.  A
`wx.App` is still needed because shapes create wx fonts when they are built:

```python
import wx

import wxdiagram

app = wx.App(redirect=False)
diagram = wxdiagram.Diagram()

for i, label in enumerate(("A", "B", "C")):
    block = wxdiagram.Block()
    block.label = label
    block.x = [20 + i * 10, 160 + i * 10]
    block.y = [20 + i * 10, 100 + i * 10]
    diagram.AddShape(block)

result = diagram.ApplyLayout("spring", options={"spacing": 40, "seed": 1})
print(result.positions)
```

## Options

| Option | Default | Meaning |
|---|---|---|
| `spacing` | `40` | gap to keep between boxes, in pixels |
| `seed` | `1` | deterministic pseudo-random seed |
| `iterations` | `500` | force iterations before early stopping |
| `keep_positions` | `False` | start from each node's current `x`/`y` |
| `reduce_crossings` | `True` | run the local crossing-reduction pass |
| `crossing_passes` | `4` | maximum refinement sweeps |

The same seed and graph produce the same positions.  `result.metadata` reports
`crossings_before`, `crossings`, `refinement_moves`, `edge_length_before` and
`edge_length`.

## Fixed nodes and direct engine use

The `ApplyLayout` helpers treat every shape as movable.  For full control, call
an engine directly with `LayoutNode` / `LayoutEdge` objects.  Set
`fixed=True` on a node to keep it where it is:

```python
from wxdiagram import LayoutEdge, LayoutNode, SpringLayout

nodes = [
    LayoutNode(id="pinned", width=160, height=80, x=500, y=300, fixed=True),
    LayoutNode(id="a", width=120, height=60),
    LayoutNode(id="b", width=120, height=60),
]
edges = [
    LayoutEdge(source="pinned", target="a"),
    LayoutEdge(source="a", target="b"),
]

result = SpringLayout(seed=3).layout(nodes, edges, options={"spacing": 40})
print(result.positions["pinned"])   # unchanged
```

`nodes_from_diagram()` / `edges_from_diagram()` / `collect_graph()` are
available when you want the canvas's collection rules but your own engine call.

## Measuring crossings

`count_crossings()` is a pure quality metric over straight centre-to-centre
segments.  `reduce_crossings()` is the same refinement pass the spring engine
uses, and can be applied to positions from another engine:

```python
from wxdiagram import count_crossings, reduce_crossings

boxes = {
    node_id: (x, y, node.width, node.height)
    for node_id, (x, y) in result.positions.items()
}
print(count_crossings(boxes, edges))

refined = reduce_crossings(nodes, edges, result.positions, spacing=40)
positions = refined.positions
```

Crossing minimisation is a local improvement, not a global guarantee: some
graphs always cross.  Set `reduce_crossings=False` to inspect the raw force
result.

## Routing

`ShapeCanvas.ApplyLayout` re-routes edges for you.  To change the style, set
the mode on each line and call `RouteEdges()`:

```python
line = self.canvas.join_shapes(client, service)
line.SetRouteMode("curved")

# after moving shapes yourself
self.canvas.RouteEdges()
```

Built-in modes are `straight`, `auto`, `avoid`, `curved` and `orthogonal`.
They are saved with the diagram.  Custom routers are an experimental API; see
[Layout and routing](../layout-routing.md) for the router protocol.

## Try the playground

The layout demo builds a small graph and lets you re-run the spring layout,
randomise sizes and switch route modes:

```bash
./bin/run-layout
# or
uv run python -m wxdiagram.layoutdemo
```

For the canvas and shape-editor demos, see the three-demo list in
[Getting started](../getting-started.md#run-the-demos).

## Heritage

The spring engine shares its conceptual ancestry with [pynsource](https://github.com/abulka/pynsource)'s
`GraphLayoutSpring`, but the two are deliberately separate implementations.
See the [appendix](../layout-routing.md#appendix-pynsource-heritage-and-variations)
for the differences and why [pynsource](https://github.com/abulka/pynsource) keeps its own pipeline.
