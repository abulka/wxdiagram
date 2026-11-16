# ---------------------------------------------------------------------------------------------
# wxdiagram - JSON persistence for diagrams
#
# Saves and loads diagrams to a small, versioned JSON format.  No pickle is used:
# the format is portable, human readable and safe to load.
#
# Format (format_version = 1):
#
#   {
#     "app": "wxdiagram",
#     "format_version": 1,
#     "shapes": [ <shape dict>, ... ]
#   }
#
# Shape dicts always carry the keys: id, type, x, y, pen, brush, font, regions,
# basePen, baseFill.  Line shapes additionally carry "connection" (from/to shape ids
# plus attachment indexes) and, for LineShape, "controlPoints", "isSpline" and "arrows".
# Composite shapes additionally carry "children" (nested shape dicts) and "constraints".
#
# Colour values are stored as either a colour name ("BLACK", looked up with
# wx.ColourDatabase) or a "#rrggbb[aa]" hexadecimal string.
# ---------------------------------------------------------------------------------------------

import json
from typing import Any, Dict, List, Optional

import wx

APP_IDENTIFIER = "wxdiagram"
FORMAT_VERSION = 1

_registry: Dict[str, type] = {}
_registered_defaults = False


def register_shape_class(cls):
    """Register a shape class so it can be saved and loaded by name."""
    _registry[cls.__name__] = cls
    return cls


def _register_default_classes():
    global _registered_defaults
    if _registered_defaults:
        return
    from . import core, divided, lines, polygon
    from .composite import CompositeShape
    from .bmpshape import BitmapShape

    classes = [
        core.Shape,  # base class - not normally used directly
        core.RectangleShape,
        core.PointShape,
        core.LinesShape,
        core.EllipseShape,
        core.ConnectableEllipseShape,
        core.TextShape,
        core.Block,
        core.ConnectionShape,
        lines.LineShape,
        divided.DividedShape,
        polygon.PolygonShape,
        BitmapShape,
        CompositeShape,
    ]
    for cls in classes:
        _registry[cls.__name__] = cls

    # Aliases for files written by the pre-rename ogl2 library.
    _registry.setdefault("LineShape2", lines.LineShape)
    _registry.setdefault("PolygonShape2", polygon.PolygonShape)
    _registry.setdefault("EllipseShapeAndy", core.ConnectableEllipseShape)
    _registered_defaults = True


def _colour_to_str(colour) -> str:
    if colour is None:
        return "BLACK"
    if isinstance(colour, str):
        return colour
    if isinstance(colour, wx.Colour):
        return "#%02x%02x%02x%02x" % (colour.Red(), colour.Green(), colour.Blue(), colour.Alpha())
    if isinstance(colour, (tuple, list)) and len(colour) >= 3:
        return "#%02x%02x%02x" % (int(colour[0]), int(colour[1]), int(colour[2]))
    return str(colour)


def _str_to_colour(value):
    if isinstance(value, str) and value.startswith("#"):
        hexpart = value.lstrip("#")
        try:
            if len(hexpart) == 8:
                return wx.Colour(
                    int(hexpart[0:2], 16),
                    int(hexpart[2:4], 16),
                    int(hexpart[4:6], 16),
                    int(hexpart[6:8], 16),
                )
            return wx.Colour(int(hexpart[0:2], 16), int(hexpart[2:4], 16), int(hexpart[4:6], 16))
        except ValueError:
            return "BLACK"
    return value


def _resolve_colour(value):
    colour = _str_to_colour(value)
    if isinstance(colour, str):
        return wx.ColourDatabase.Find(colour)
    return colour


def _font_to_dict(font) -> Optional[dict]:
    if font is None:
        return None
    return {
        "face": font.GetFaceName(),
        "pointSize": font.GetPointSize(),
        "family": font.GetFamily(),
        "style": font.GetStyle(),
        "weight": font.GetWeight(),
    }


def _dict_to_font(data):
    if not data:
        return None
    return wx.Font(
        data.get("pointSize", 12),
        data.get("family", wx.FONTFAMILY_SWISS),
        data.get("style", wx.FONTSTYLE_NORMAL),
        data.get("weight", wx.FONTWEIGHT_NORMAL),
        faceName=data.get("face", ""),
    )


def _pen_to_dict(pen) -> Optional[dict]:
    if pen is None:
        return None
    return {
        "colour": _colour_to_str(pen.GetColour()),
        "width": pen.GetWidth(),
        "style": pen.GetStyle(),
    }


def _dict_to_pen(data):
    if not data:
        return None
    colour = _resolve_colour(data["colour"])
    return wx.Pen(colour, data.get("width", 1), data.get("style", wx.PENSTYLE_SOLID))


def _brush_to_dict(brush) -> Optional[dict]:
    if brush is None:
        return None
    return {"colour": _colour_to_str(brush.GetColour()), "style": brush.GetStyle()}


def _dict_to_brush(data):
    if not data:
        return None
    colour = _resolve_colour(data["colour"])
    return wx.Brush(colour, data.get("style", wx.BRUSHSTYLE_SOLID))


def _region_to_dict(region) -> dict:
    return {
        "name": region._regionName,
        "lines": [
            {"x": line.GetX(), "y": line.GetY(), "text": line.GetText()}
            for line in region.GetFormattedText()
        ],
        "colour": _colour_to_str(region._textColour),
        "font": _font_to_dict(region.GetFont()),
        "formatMode": region.GetFormatMode(),
        "minSize": [region._minWidth, region._minHeight],
        "size": [region._width, region._height],
        "position": [region._x, region._y],
        "proportions": [region._regionProportionX, region._regionProportionY],
        "penColour": region.GetPenColour() if isinstance(region.GetPenColour(), str) else "BLACK",
        "penStyle": region.GetPenStyle(),
    }


def _dict_to_region(data):
    from .basic import ShapeRegion, ShapeTextLine

    region = ShapeRegion()
    region.SetName(data.get("name", ""))
    region.SetColour(_str_to_colour(data.get("colour", "BLACK")))
    if data.get("font"):
        region.SetFont(_dict_to_font(data["font"]))
    region.SetFormatMode(data.get("formatMode", 0))
    min_size = data.get("minSize", [5.0, 5.0])
    region.SetMinSize(min_size[0], min_size[1])
    size = data.get("size", [0.0, 0.0])
    region.SetSize(size[0], size[1])
    pos = data.get("position", [0.0, 0.0])
    region.SetPosition(pos[0], pos[1])
    proportions = data.get("proportions", [-1.0, -1.0])
    region.SetProportions(proportions[0], proportions[1])
    region.SetPenColour(data.get("penColour", "BLACK"))
    region.SetPenStyle(data.get("penStyle", wx.PENSTYLE_SOLID))
    for line in data.get("lines", []):
        region.GetFormattedText().append(ShapeTextLine(line["x"], line["y"], line["text"]))
    return region


def shape_to_dict(shape, id_map: Dict[int, int]) -> Dict[str, Any]:
    data = {
        "id": id_map[id(shape)],
        "type": type(shape).__name__,
        "x": list(shape.x),
        "y": list(shape.y),
        "pen": _pen_to_dict(getattr(shape, "_pen", None)),
        "brush": _brush_to_dict(getattr(shape, "_brush", None)),
        "font": _font_to_dict(getattr(shape, "_font", None)),
        "regions": [_region_to_dict(region) for region in getattr(shape, "_regions", [])],
        "basePen": list(getattr(shape, "pen", [])),
        "baseFill": list(getattr(shape, "fill", [])),
    }

    # lines with typed endpoints (ConnectionShape in core.py)
    if type(shape).__name__ == "ConnectionShape":
        data["connection"] = {
            "from": id_map.get(id(shape.input[0])) if getattr(shape, "input", None) else None,
            "fromAttach": shape.input[1] if getattr(shape, "input", None) else 0,
            "to": id_map.get(id(shape.output[0])) if getattr(shape, "output", None) else None,
            "toAttach": shape.output[1] if getattr(shape, "output", None) else 0,
        }

    # LineShape-style line with _from / _to pointers
    elif getattr(shape, "_from", None) is not None or getattr(shape, "_to", None) is not None:
        data["connection"] = {
            "from": id_map.get(id(shape._from))
            if getattr(shape, "_from", None) is not None
            else None,
            "to": id_map.get(id(shape._to)) if getattr(shape, "_to", None) is not None else None,
            "fromAttach": getattr(shape, "_attachmentFrom", 0),
            "toAttach": getattr(shape, "_attachmentTo", 0),
        }

    # LineShape geometry
    if hasattr(shape, "_lineControlPoints"):
        data["controlPoints"] = [[p[0], p[1]] for p in shape._lineControlPoints]
        data["isSpline"] = getattr(shape, "_isSpline", False)
        data["arrows"] = [
            {
                "type": a._GetType(),
                "end": a.GetArrowEnd(),
                "size": a.GetSize(),
                "xOffset": a.GetXOffset(),
                "spacing": a.GetSpacing(),
                "name": a.GetName(),
                "id": a._id if isinstance(a._id, int) else -1,
            }
            for a in getattr(shape, "_arcArrows", [])
        ]

    # convenience attributes
    if hasattr(shape, "label"):
        data["label"] = shape.label
    if hasattr(shape, "label_colour"):
        data["labelColour"] = _colour_to_str(shape.label_colour)
    if hasattr(shape, "GetFilename"):
        filename = shape.GetFilename()
        if filename:
            data["bitmapFile"] = filename

    # shapes with their own children
    children = getattr(shape, "_compositeChildren", None)
    if children is not None:
        data["children"] = [shape_to_dict(child, id_map) for child in children]
        data["constraints"] = shape.serialize_constraints(id_map)

    return data


def dict_to_shape(data, id_to_shape: Dict[int, Any]) -> Any:
    cls = _registry.get(data["type"])
    if cls is None:
        raise KeyError(f"Shape type {data['type']!r} is not registered; cannot load this file")

    if data["type"] == "DividedShape":
        shape = cls(100, 100)
    elif data["type"] == "LinesShape":
        shape = cls([])
    else:
        try:
            shape = cls()
        except TypeError:
            shape = cls([])

    shape.x = list(data.get("x", []))
    shape.y = list(data.get("y", []))
    shape._persist_id = data["id"]
    if hasattr(shape, "SetId"):
        shape.SetId(data["id"])

    if data.get("pen") is not None:
        shape._pen = _dict_to_pen(data["pen"])
    if data.get("brush") is not None:
        shape._brush = _dict_to_brush(data["brush"])
    if data.get("font") is not None:
        shape._font = _dict_to_font(data["font"])
    if data.get("basePen") is not None:
        shape.pen = list(data["basePen"])
    if data.get("baseFill") is not None:
        shape.fill = list(data["baseFill"])

    shape._regions = [_dict_to_region(r) for r in data.get("regions", [])]

    if data.get("label") is not None:
        shape.label = data["label"]
    if data.get("labelColour") is not None and hasattr(shape, "label_colour"):
        shape.label_colour = _resolve_colour(data["labelColour"])
    if data.get("bitmapFile"):
        shape.SetFilename(data["bitmapFile"])

    if data.get("controlPoints") is not None:
        shape._lineControlPoints = [wx.RealPoint(p[0], p[1]) for p in data["controlPoints"]]
        shape._isSpline = data.get("isSpline", False)
        shape._arcArrows = []
        for a in data.get("arrows", []):
            shape.AddArrow(
                a["type"],
                a.get("end", 0),
                a.get("size", 10.0),
                a.get("xOffset", 0.0),
                a.get("name", ""),
                None,
                a.get("id", -1),
            )
            # AddArrow creates a fresh ArrowHead; set spacing afterwards
            if shape._arcArrows and a.get("spacing") is not None:
                shape._arcArrows[-1].SetSpacing(a["spacing"])

    id_to_shape[data["id"]] = shape

    # nested children (composite / container) are attached after all shapes exist so
    # that connections can reference them; stash the raw dicts for now
    shape._children_to_load = data.get("children")
    shape._constraints_to_load = data.get("constraints")

    return shape


def _resolve_children(shape, id_to_shape, build_recursive):

    children = []
    for child_data in getattr(shape, "_children_to_load", None) or []:
        child = build_recursive(child_data)
        children.append(child)

    if hasattr(shape, "_compositeChildren"):
        for child in children:
            shape.add_child(child)

    for attr in ("_children_to_load", "_constraints_to_load"):
        if hasattr(shape, attr):
            delattr(shape, attr)

    return children


def _apply_connections(shapes, id_to_shape):
    for shape in shapes:
        conn = getattr(shape, "connection_to_load", None)
        if not conn:
            continue
        frm = id_to_shape.get(conn.get("from"))
        to = id_to_shape.get(conn.get("to"))
        if type(shape).__name__ == "ConnectionShape":
            shape.input = (frm, conn.get("fromAttach", 0)) if frm is not None else None
            shape.output = (to, conn.get("toAttach", 0)) if to is not None else None
        else:
            shape._from = frm
            shape._to = to
            shape._attachmentFrom = conn.get("fromAttach", 0)
            shape._attachmentTo = conn.get("toAttach", 0)
        delattr(shape, "connection_to_load")


def diagram_to_dict(diagram) -> Dict[str, Any]:
    _register_default_classes()

    flat: List[Any] = []

    def collect(shape):
        flat.append(shape)
        for child in getattr(shape, "_compositeChildren", []) or []:
            collect(child)

    for shape in getattr(diagram, "shapes", []):
        collect(shape)

    id_map: Dict[int, int] = {}
    seen_ids = set()
    for shape in flat:
        shape_id = shape.GetId() if getattr(shape, "GetId", None) is not None else 0
        if shape_id == 0 or shape_id in seen_ids:
            shape.AssignNewIds()
            shape_id = shape.GetId()
        seen_ids.add(shape_id)
        shape._persist_id = shape_id
        id_map[id(shape)] = shape_id

    return {
        "app": APP_IDENTIFIER,
        "format_version": FORMAT_VERSION,
        "shapes": [shape_to_dict(s, id_map) for s in getattr(diagram, "shapes", [])],
    }


def diagram_from_dict(data) -> Any:
    _register_default_classes()

    if data.get("app") != APP_IDENTIFIER:
        raise ValueError(f"Not a wxdiagram diagram file (expected app={APP_IDENTIFIER!r})")
    version = data.get("format_version", 0)
    if version > FORMAT_VERSION:
        raise ValueError(
            f"Unsupported wxdiagram format_version {version} (max supported {FORMAT_VERSION})"
        )

    from .core import Diagram

    diagram = Diagram()
    id_to_shape: Dict[int, Any] = {}
    all_shapes: List[Any] = []

    def build(shape_data):
        shape = dict_to_shape(shape_data, id_to_shape)
        all_shapes.append(shape)
        _resolve_children(shape, id_to_shape, build)
        if shape_data.get("connection"):
            shape.connection_to_load = shape_data["connection"]
        if shape_data.get("constraints"):
            if hasattr(shape, "deserialize_constraints"):
                shape.deserialize_constraints(shape_data["constraints"], id_to_shape)
        return shape

    for sd in data.get("shapes", []):
        build(sd)

    _apply_connections(all_shapes, id_to_shape)

    # Diagram.AddShape inserts at the front; iterate reversed to keep the file order
    for sd in reversed(data.get("shapes", [])):
        diagram.AddShape(id_to_shape[sd["id"]])

    return diagram


def save(diagram, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diagram_to_dict(diagram), f, indent=2)


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return diagram_from_dict(data)
