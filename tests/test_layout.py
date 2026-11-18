"""Layout protocol, registry and SpringLayout (pure Python, no wx needed)."""

import pytest

import wxdiagram
from wxdiagram.layout import (
    LayoutEdge,
    LayoutNode,
    available_layouts,
    get_layout,
    register_layout,
)
from wxdiagram.layout_spring import SpringLayout
from wxdiagram.routing import available_routers, get_router


def _nodes(n, w=100.0, h=60.0):
    return [LayoutNode(id=f"n{i}", width=w, height=h) for i in range(n)]


def test_registry_has_spring_and_default_router():
    assert "spring" in available_layouts()
    assert "spring" in wxdiagram.available_layouts()
    assert "default" in available_routers()
    assert isinstance(get_layout("spring"), SpringLayout)
    with pytest.raises(KeyError):
        get_layout("no-such-layout")
    with pytest.raises(KeyError):
        get_router("no-such-router")


def test_custom_layout_registration():
    class Dummy:
        name = "dummy-test-layout"

        def layout(self, nodes, edges, *, options=None, on_step=None):
            return wxdiagram.LayoutResult(positions={n.id: (0.0, 0.0) for n in nodes})

    register_layout(Dummy)
    assert "dummy-test-layout" in available_layouts()
    assert get_layout("dummy-test-layout").name == "dummy-test-layout"


def test_spring_empty_and_single():
    engine = SpringLayout(seed=1)
    assert engine.layout([], []).positions == {}
    result = engine.layout(_nodes(1), [])
    assert set(result.positions) == {"n0"}
    x, y = result.positions["n0"]
    assert x >= 0 and y >= 0


def test_spring_deterministic_for_seed():
    nodes = _nodes(6)
    edges = [LayoutEdge(source=f"n{i}", target=f"n{(i + 1) % 6}") for i in range(6)]

    def run():
        return SpringLayout(seed=7).layout(nodes, edges).positions

    first, second = run(), run()
    assert first == second
    # The seed is honoured when jitter is needed: coincident starts diverge.
    stacked = [LayoutNode(id=f"s{i}", width=100, height=60, x=0.0, y=0.0) for i in range(4)]
    no_edges: list = []
    opts = {"keep_positions": True}
    a = SpringLayout(seed=7).layout(stacked, no_edges, options=opts).positions
    b = SpringLayout(seed=8).layout(stacked, no_edges, options=opts).positions
    assert a != b


def test_spring_disconnected_selfloop_duplicates_and_fixed():
    nodes = _nodes(5)
    fixed = LayoutNode(id="fixed", width=100, height=60, x=500.0, y=400.0, fixed=True)
    nodes = nodes + [fixed]
    edges = [
        LayoutEdge(source="n0", target="n1"),
        LayoutEdge(source="n1", target="n0"),  # duplicate/reverse
        LayoutEdge(source="n2", target="n2"),  # self-loop
        LayoutEdge(source="n3", target="n4", weight=3.0),
    ]
    result = SpringLayout(seed=1).layout(nodes, edges)
    assert set(result.positions) == {n.id for n in nodes}
    # Fixed node does not move.
    assert result.positions["fixed"] == (500.0, 400.0)
    # No overlaps (with the default spacing) for a small graph.
    boxes = {n.id: (result.positions[n.id][0], result.positions[n.id][1], n.width, n.height) for n in nodes}
    ids = list(boxes)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            ax, ay, aw, ah = boxes[ids[i]]
            bx, by, bw, bh = boxes[ids[j]]
            assert ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay


def test_spring_rejects_duplicate_node_ids():
    nodes = [LayoutNode(id="same", width=100, height=60) for _ in range(2)]
    with pytest.raises(ValueError):
        SpringLayout(seed=1).layout(nodes, [])


def test_spring_metadata_reports_crossings():
    nodes = _nodes(5)
    edges = [LayoutEdge(source=f"n{i}", target=f"n{(i + 1) % 5}") for i in range(5)]
    result = SpringLayout(seed=1).layout(nodes, edges, options={"spacing": 40})
    assert "crossings" in result.metadata
    assert "crossings_before" in result.metadata
    assert result.metadata["crossings"] <= result.metadata["crossings_before"]
    assert "edge_length" in result.metadata


def test_spring_keep_positions_and_on_step_abort():
    nodes = [
        LayoutNode(id="a", width=100, height=60, x=10.0, y=20.0),
        LayoutNode(id="b", width=100, height=60, x=300.0, y=200.0),
    ]
    edges = [LayoutEdge(source="a", target="b")]
    calls = []

    def on_step(step, info=None):
        calls.append(step)
        return False  # abort after the first iteration

    result = SpringLayout(seed=1).layout(
        nodes, edges, options={"keep_positions": True}, on_step=on_step
    )
    assert set(result.positions) == {"a", "b"}
    assert calls, "on_step was not called"
    assert result.metadata["engine"] == "spring"


def test_collect_graph_skips_lines_without_canvas():
    # Pure-diagram helper coverage without wx: fake minimal shapes.
    class FakeShape:
        def __init__(self, x, y):
            self.x, self.y = x, y

        def GetId(self):
            return 0

    class FakeDiagram:
        shapes = [FakeShape([0, 100], [0, 60]), FakeShape([200, 300], [0, 60])]

    nodes, id_by_shape = wxdiagram.layout.nodes_from_diagram(FakeDiagram())
    assert len(nodes) == 2
    assert nodes[0].width == 100.0
