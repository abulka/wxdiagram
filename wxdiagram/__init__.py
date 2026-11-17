"""
wxdiagram - a zoomable shape-and-connector canvas for wxPython.

This module exports the public API.  For implementation details see the
individual modules.  The most useful entry points:

    import wxdiagram
    wxdiagram.initialize()
    diagram = wxdiagram.Diagram()
    canvas = wxdiagram.ShapeCanvas(parent)

Persistence::

    import wxdiagram.persistence as persistence
    persistence.save(diagram, "diagram.json")
    diagram = persistence.load("diagram.json")
"""

try:
    from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
    from importlib.metadata import version as _version

    try:
        __version__ = _version("wxdiagram")
    except _PackageNotFoundError:  # running from a source tree without metadata
        __version__ = "0.0.0+unknown"
except Exception:  # pragma: no cover
    __version__ = "0.0.0+unknown"

from .geometry import (
    # constants
    ATTACHMENT_MODE_NONE,
    ATTACHMENT_MODE_EDGE,
    ATTACHMENT_MODE_BRANCHING,
    BRANCHING_ATTACHMENT_NORMAL,
    BRANCHING_ATTACHMENT_BLOB,
    FORMAT_CENTRE_HORIZ,
    FORMAT_CENTRE_VERT,
    FORMAT_NONE,
    FORMAT_SIZE_TO_CONTENTS,
    SHADOW_LEFT,
    SHADOW_NONE,
    SHADOW_RIGHT,
    OP_CLICK_LEFT,
    OP_CLICK_RIGHT,
    OP_DRAG_LEFT,
    OP_DRAG_RIGHT,
    OP_ALL,
    ARROW_ARROW,
    ARROW_DOUBLE_OBLIQUE,
    ARROW_FILLED_CIRCLE,
    ARROW_HOLLOW_CIRCLE,
    ARROW_METAFILE,
    ARROW_SINGLE_OBLIQUE,
    ARROW_POSITION_END,
    ARROW_POSITION_MIDDLE,
    ARROW_POSITION_START,
    LINE_ALIGNMENT_HORIZ,
    LINE_ALIGNMENT_NONE,
    LINE_ALIGNMENT_TO_NEXT_HANDLE,
    LINE_ALIGNMENT_VERT,
    CONTROL_POINT_SIZE,
    CONTROL_POINT_VERTICAL,
    CONTROL_POINT_HORIZONTAL,
    CONTROL_POINT_DIAGONAL,
    CONTROL_POINT_ENDPOINT_TO,
    CONTROL_POINT_ENDPOINT_FROM,
    CONTROL_POINT_LINE,
    KEY_CTRL,
    KEY_SHIFT,
    # helpers
    CentreText,
    CheckLineIntersection,
    DrawFormattedText,
    FindEndForBox,
    FindEndForCircle,
    FindEndForPolyline,
    DrawArcToEllipse,
    FormatText,
    GetArrowPoints,
    GetCentredTextExtent,
    GetPointOnLine,
    GraphicsStraightenLine,
    PolylineHitTest,
    RoughlyEqual,
    line_control_points_to_xy_points,
)

from .basic import initialize, ShapeRegion, ShapeTextLine, get_normal_font
from .core import (
    Attributable,
    Block,
    Connectable,
    ConnectionShape,
    Diagram,
    EllipseShape,
    ConnectableEllipseShape,
    LinesShape,
    PointShape,
    RectangleShape,
    ResizableRectangleShape,
    Resizeable,
    Selectable,
    Shape,
    ShapeCanvas,
    ShapeEvtHandler,
    TextShape,
    SelectableTextShape,
)
from .polygon import PolygonShape
from .lines import ArrowHead, ControlPoint, LineControlPoint, LineShape
from .routing import route_edge
from .bmpshape import BitmapShape, ResizableBitmapShape
from .divided import DividedShape
from .composite import (
    Constraint,
    ConstraintType,
    CompositeShape,
    CONSTRAINT_ABOVE,
    CONSTRAINT_ALIGNED_BOTTOM,
    CONSTRAINT_ALIGNED_LEFT,
    CONSTRAINT_ALIGNED_RIGHT,
    CONSTRAINT_ALIGNED_TOP,
    CONSTRAINT_BELOW,
    CONSTRAINT_CENTRED_BOTH,
    CONSTRAINT_CENTRED_HORIZONTALLY,
    CONSTRAINT_CENTRED_VERTICALLY,
    CONSTRAINT_LEFT_OF,
    CONSTRAINT_MIDALIGNED_BOTTOM,
    CONSTRAINT_MIDALIGNED_LEFT,
    CONSTRAINT_MIDALIGNED_RIGHT,
    CONSTRAINT_MIDALIGNED_TOP,
    CONSTRAINT_RIGHT_OF,
)
from . import persistence

__all__ = [
    # constants
    "ATTACHMENT_MODE_NONE",
    "ATTACHMENT_MODE_EDGE",
    "ATTACHMENT_MODE_BRANCHING",
    "BRANCHING_ATTACHMENT_NORMAL",
    "BRANCHING_ATTACHMENT_BLOB",
    "FORMAT_CENTRE_HORIZ",
    "FORMAT_CENTRE_VERT",
    "FORMAT_NONE",
    "FORMAT_SIZE_TO_CONTENTS",
    "SHADOW_LEFT",
    "SHADOW_NONE",
    "SHADOW_RIGHT",
    "OP_CLICK_LEFT",
    "OP_CLICK_RIGHT",
    "OP_DRAG_LEFT",
    "OP_DRAG_RIGHT",
    "OP_ALL",
    "ARROW_ARROW",
    "ARROW_DOUBLE_OBLIQUE",
    "ARROW_FILLED_CIRCLE",
    "ARROW_HOLLOW_CIRCLE",
    "ARROW_METAFILE",
    "ARROW_SINGLE_OBLIQUE",
    "ARROW_POSITION_END",
    "ARROW_POSITION_MIDDLE",
    "ARROW_POSITION_START",
    "LINE_ALIGNMENT_HORIZ",
    "LINE_ALIGNMENT_NONE",
    "LINE_ALIGNMENT_TO_NEXT_HANDLE",
    "LINE_ALIGNMENT_VERT",
    "CONTROL_POINT_SIZE",
    "CONTROL_POINT_VERTICAL",
    "CONTROL_POINT_HORIZONTAL",
    "CONTROL_POINT_DIAGONAL",
    "CONTROL_POINT_ENDPOINT_TO",
    "CONTROL_POINT_ENDPOINT_FROM",
    "CONTROL_POINT_LINE",
    "KEY_CTRL",
    "KEY_SHIFT",
    "CONSTRAINT_ABOVE",
    "CONSTRAINT_ALIGNED_BOTTOM",
    "CONSTRAINT_ALIGNED_LEFT",
    "CONSTRAINT_ALIGNED_RIGHT",
    "CONSTRAINT_ALIGNED_TOP",
    "CONSTRAINT_BELOW",
    "CONSTRAINT_CENTRED_BOTH",
    "CONSTRAINT_CENTRED_HORIZONTALLY",
    "CONSTRAINT_CENTRED_VERTICALLY",
    "CONSTRAINT_LEFT_OF",
    "CONSTRAINT_MIDALIGNED_BOTTOM",
    "CONSTRAINT_MIDALIGNED_LEFT",
    "CONSTRAINT_MIDALIGNED_RIGHT",
    "CONSTRAINT_MIDALIGNED_TOP",
    "CONSTRAINT_RIGHT_OF",
    # helpers
    "CentreText",
    "CheckLineIntersection",
    "DrawFormattedText",
    "FindEndForBox",
    "FindEndForCircle",
    "FindEndForPolyline",
    "DrawArcToEllipse",
    "FormatText",
    "GetArrowPoints",
    "GetCentredTextExtent",
    "GetPointOnLine",
    "GraphicsStraightenLine",
    "PolylineHitTest",
    "RoughlyEqual",
    "line_control_points_to_xy_points",
    # classes & functions
    "initialize",
    "ShapeRegion",
    "ShapeTextLine",
    "get_normal_font",
    "Attributable",
    "Block",
    "Connectable",
    "ConnectionShape",
    "EllipseShape",
    "ConnectableEllipseShape",
    "LineShape",
    "route_edge",
    "LinesShape",
    "PointShape",
    "RectangleShape",
    "ResizableRectangleShape",
    "Resizeable",
    "Selectable",
    "Shape",
    "ShapeEvtHandler",
    "TextShape",
    "SelectableTextShape",
    "ShapeCanvas",
    "Diagram",
    "PolygonShape",
    "ArrowHead",
    "ControlPoint",
    "LineControlPoint",
    "BitmapShape",
    "ResizableBitmapShape",
    "DividedShape",
    "Constraint",
    "ConstraintType",
    "CompositeShape",
    "persistence",
]
