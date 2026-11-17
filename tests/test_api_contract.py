"""
Public API contract test.

These names are the documented library surface.  Keep them importable unless a
breaking release is planned; pynsource is the main downstream consumer.
"""

import wxdiagram

PUBLIC_NAMES = [
    # from wxdiagram import ARROW_*
    "ARROW_ARROW",
    "ARROW_DOUBLE_OBLIQUE",
    "ARROW_FILLED_CIRCLE",
    "ARROW_HOLLOW_CIRCLE",
    "ARROW_METAFILE",
    "ARROW_POSITION_END",
    "ARROW_POSITION_MIDDLE",
    "ARROW_POSITION_START",
    "ARROW_SINGLE_OBLIQUE",
    # from wxdiagram import Connectable, Resizeable, Selectable, Attributable
    "Connectable",
    "Resizeable",
    "Selectable",
    "Attributable",
    # from wxdiagram import ...
    "GetArrowPoints",
    "GetPointOnLine",
    "line_control_points_to_xy_points",
    "LineShape",
    "initialize",
    "Shape",
    "RectangleShape",
    "LinesShape",
    "ShapeRegion",
    "FORMAT_NONE",
    "FORMAT_CENTRE_HORIZ",
    "FORMAT_CENTRE_VERT",
    # package-level names
    "ShapeCanvas",
    "Diagram",
    "Shape",
    "Block",
    "DividedShape",
    "BitmapShape",
    "PolygonShape",
    "ShapeEvtHandler",
]


def test_public_names_exist():
    missing = [name for name in PUBLIC_NAMES if getattr(wxdiagram, name, None) is None]
    assert not missing, f"wxdiagram is missing public names: {missing}"


# The names pynsource imports or relies on. Keep this list in sync with
# pynsource's src/tests/test_wxdiagram_contract.py.
PYNSOURCE_NAMES = [
    "Attributable",
    "BitmapShape",
    "Connectable",
    "Diagram",
    "DividedShape",
    "LineShape",
    "PolygonShape",
    "RectangleShape",
    "Resizeable",
    "Selectable",
    "Shape",
    "ShapeCanvas",
    "ShapeEvtHandler",
    "ShapeRegion",
    "GetArrowPoints",
    "GetPointOnLine",
    "initialize",
    "line_control_points_to_xy_points",
]


def test_pynsource_names_exist():
    missing = [name for name in PYNSOURCE_NAMES if getattr(wxdiagram, name, None) is None]
    assert not missing, f"wxdiagram is missing names pynsource needs: {missing}"


def test_canvas_extension_points():
    """Subclass hooks used by pynsource and other applications."""
    assert hasattr(wxdiagram.Shape, "MoveTo")
    assert hasattr(wxdiagram.ShapeCanvas, "getContentBounds")
    assert hasattr(wxdiagram.ShapeCanvas, "getContentOrigin")
    for name in ["update_virtual_size", "ZoomToFit", "ZoomIn", "ZoomOut", "ZoomReset"]:
        assert hasattr(wxdiagram.ShapeCanvas, name), name
    # class-level defaults that applications tune
    assert wxdiagram.ShapeCanvas.ZOOM_MIN_SCALE <= 1.0


def test_all_exported_names_are_importable():
    for name in wxdiagram.__all__:
        assert getattr(wxdiagram, name, None) is not None, (
            f"wxdiagram.{name} is declared in __all__ but not importable"
        )


def test_version_is_set():
    assert isinstance(wxdiagram.__version__, str) and wxdiagram.__version__
