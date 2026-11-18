"""Pluggable graph layout: protocols, registry and diagram helpers.

This module is pure Python (no wx import) so layouts stay testable without
a window.  Positions use the same convention as ``Shape.MoveTo``: the
**top-left** corner of each node box.

A layout engine implements::

    class MyLayout:
        name = "mine"
        def layout(self, nodes, edges, *, options=None, on_step=None):
            ...

and is registered with :func:`register_layout` (or passed directly to
:meth:`Diagram.ApplyLayout <wxdiagram.core.Diagram.ApplyLayout>`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Protocol, Tuple


@dataclass(frozen=True)
class LayoutNode:
    """One box to place; ``x``/``y`` are the current top-left position."""

    id: str
    width: float
    height: float
    x: Optional[float] = None
    y: Optional[float] = None
    fixed: bool = False


@dataclass(frozen=True)
class LayoutEdge:
    """One connection between two node ids."""

    source: str
    target: str
    kind: str = ""
    weight: float = 1.0


@dataclass
class LayoutResult:
    """Engine outcome: top-left positions keyed by node id.

    ``metadata`` is engine-specific; the bundled spring engine reports
    ``crossings``, ``crossings_before``, ``refinement_moves``,
    ``edge_length`` and ``edge_length_before``.
    """

    positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    bounds: Optional[Tuple[float, float, float, float]] = None
    metadata: Dict = field(default_factory=dict)


class LayoutEngine(Protocol):
    """Structural protocol for layout engines."""

    name: str

    def layout(
        self,
        nodes: List[LayoutNode],
        edges: List[LayoutEdge],
        *,
        options: Optional[dict] = None,
        on_step: Optional[Callable[[int, dict], bool]] = None,
    ) -> LayoutResult:
        """Place ``nodes``; return top-left positions.  ``on_step`` may
        return False to abort early."""
        ...  # pragma: no cover


_LAYOUT_REGISTRY: Dict[str, object] = {}


def _ensure_builtin_layouts():
    """Import the bundled engines on first use (avoids import cycles)."""
    if "spring" in _LAYOUT_REGISTRY:
        return
    try:
        import importlib

        importlib.import_module(".layout_spring", __package__)
    except Exception:  # pragma: no cover - defensive for partial installs
        pass


def register_layout(name_or_engine, engine=None):
    """Register a layout engine instance (or class).

    Usage::

        register_layout("spring", SpringLayout())
        register_layout(SpringLayout)  # uses ``SpringLayout.name``
    """
    if engine is None:
        engine = name_or_engine
        name = getattr(engine, "name", None)
        if isinstance(engine, type):
            engine = engine()
            name = getattr(engine, "name", name)
        if not name:
            raise ValueError("Layout engine has no name; pass one explicitly")
    else:
        name = name_or_engine
    _LAYOUT_REGISTRY[name] = engine
    return engine


def get_layout(name_or_engine):
    """Resolve a layout engine from an instance, class or registered name."""
    if isinstance(name_or_engine, str):
        _ensure_builtin_layouts()
        try:
            return _LAYOUT_REGISTRY[name_or_engine]
        except KeyError:
            raise KeyError(f"Unknown layout engine: {name_or_engine!r}") from None
    if isinstance(name_or_engine, type):
        return name_or_engine()
    return name_or_engine


def available_layouts():
    """Sorted list of registered layout names."""
    _ensure_builtin_layouts()
    return sorted(_LAYOUT_REGISTRY)


def _shape_box(shape):
    """Return ``(left, top, width, height)`` for a shape, or None."""
    xs = list(getattr(shape, "x", []) or [])
    ys = list(getattr(shape, "y", []) or [])
    if len(xs) >= 2 and len(ys) >= 2:
        try:
            left, right = min(xs), max(xs)
            top, bottom = min(ys), max(ys)
        except TypeError:
            return None
        return float(left), float(top), float(right - left), float(bottom - top)
    get_bbox = getattr(shape, "GetBoundingBoxMin", None)
    if callable(get_bbox):
        try:
            width, height = get_bbox()
        except Exception:
            return None
        get_x = getattr(shape, "GetX", None)
        get_y = getattr(shape, "GetY", None)
        if callable(get_x) and callable(get_y):
            try:
                cx, cy = float(get_x()), float(get_y())
            except Exception:
                return None
            return cx - width / 2.0, cy - height / 2.0, float(width), float(height)
    return None


def _is_edge_shape(shape) -> bool:
    """True for line/edge shapes (they become LayoutEdges, not nodes)."""
    return hasattr(shape, "_lineControlPoints") or (
        hasattr(shape, "_from") and hasattr(shape, "_to")
    )


def _node_id(shape, index: int) -> str:
    get_id = getattr(shape, "GetId", None)
    try:
        shape_id = get_id() if callable(get_id) else 0
    except Exception:
        shape_id = 0
    if shape_id:
        return str(shape_id)
    return f"shape-{index}"


def nodes_from_diagram(diagram) -> Tuple[List[LayoutNode], Dict[int, str]]:
    """Collect layout nodes from top-level non-edge shapes.

    Returns ``(nodes, id_by_shape)`` where ``id_by_shape`` maps
    ``id(shape)`` to the layout node id, for edge resolution.
    """
    nodes: List[LayoutNode] = []
    id_by_shape: Dict[int, str] = {}
    shapes = list(getattr(diagram, "shapes", []) or [])
    index = 0
    for shape in shapes:
        if _is_edge_shape(shape):
            continue
        box = _shape_box(shape)
        if box is None:
            continue
        left, top, width, height = box
        if width <= 0 or height <= 0:
            continue
        node_id = _node_id(shape, index)
        index += 1
        # Guard against duplicate ids (e.g. unassigned shapes sharing id 0).
        base = node_id
        suffix = 0
        taken = {node.id for node in nodes}
        while node_id in taken:
            suffix += 1
            node_id = f"{base}#{suffix}"
        fixed = bool(getattr(shape, "_layout_fixed", False))
        if callable(getattr(shape, "IsLayoutFixed", None)):
            try:
                fixed = bool(shape.IsLayoutFixed())
            except Exception:
                pass
        nodes.append(
            LayoutNode(
                id=node_id,
                width=float(width),
                height=float(height),
                x=float(left),
                y=float(top),
                fixed=fixed,
            )
        )
        id_by_shape[id(shape)] = node_id
    return nodes, id_by_shape


def edges_from_diagram(diagram, id_by_shape: Dict[int, str]) -> List[LayoutEdge]:
    """Collect layout edges from attached ``LineShape`` objects."""
    edges: List[LayoutEdge] = []
    for shape in list(getattr(diagram, "shapes", []) or []):
        frm = getattr(shape, "_from", None)
        to = getattr(shape, "_to", None)
        if frm is None or to is None:
            continue
        source = id_by_shape.get(id(frm))
        target = id_by_shape.get(id(to))
        if source is None or target is None:
            continue
        kind = str(
            getattr(shape, "_uml_edge_type", "")
            or getattr(shape, "uml_edge_type", "")
            or getattr(shape, "edge_type", "")
            or ""
        )
        weight = getattr(shape, "_layout_weight", 1.0)
        try:
            weight = float(weight)
        except (TypeError, ValueError):
            weight = 1.0
        edges.append(LayoutEdge(source=source, target=target, kind=kind, weight=weight))
    return edges


def collect_graph(diagram) -> Tuple[List[LayoutNode], List[LayoutEdge]]:
    """Collect ``(nodes, edges)`` from a diagram in one call."""
    nodes, id_by_shape = nodes_from_diagram(diagram)
    return nodes, edges_from_diagram(diagram, id_by_shape)


__all__ = [
    "LayoutNode",
    "LayoutEdge",
    "LayoutResult",
    "LayoutEngine",
    "register_layout",
    "get_layout",
    "available_layouts",
    "nodes_from_diagram",
    "edges_from_diagram",
    "collect_graph",
]
