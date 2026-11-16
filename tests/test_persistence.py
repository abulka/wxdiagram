"""Round-trip tests for the wxdiagram JSON persistence format."""

import json

import pytest

import wxdiagram
from wxdiagram import (
    ARROW_ARROW,
    ARROW_POSITION_END,
    Block,
    ConnectionShape,
    Diagram,
    DividedShape,
    LineShape,
    RectangleShape,
    ShapeRegion,
)


def make_diagram():
    blueprint = Diagram()

    rect = RectangleShape(10, 10, 120, 90)
    rect.AddText("rect label")
    rect._persist_id = 1
    blueprint.AppendShape(rect)

    block = Block()
    block.label = "myblock"
    block.SetX(200)
    block.SetY(100)
    block._persist_id = 2
    blueprint.AppendShape(block)

    divided = DividedShape(120, 80)
    divided.SetX(400)
    divided.SetY(100)
    region = ShapeRegion()
    region.SetName("header")
    region.SetText("MyClass")
    divided.AddRegion(region)
    divided._persist_id = 4
    blueprint.AppendShape(divided)

    polygon = wxdiagram.PolygonShape()
    polygon.Create([(0, 0), (40, 0), (20, 40)])
    polygon.move_to(300, 250)
    polygon._persist_id = 5
    blueprint.AppendShape(polygon)

    line = LineShape()
    line.MakeLineControlPoints(2)
    line.SetEnds(130, 100, 200, 110)
    line.SetFrom(rect)
    line.SetTo(block)
    line.AddArrow(
        ARROW_ARROW, ARROW_POSITION_END, size=10.0, xOffset=0.0, name="", mf=None, arrowId=-1
    )
    line._persist_id = 6
    blueprint.AppendShape(line)

    return blueprint


def test_round_trip_to_same_json(wx_app, tmp_path):
    diagram = make_diagram()
    first = tmp_path / "first.json"
    wxdiagram.persistence.save(diagram, first)

    loaded = wxdiagram.persistence.load(first)
    second = tmp_path / "second.json"
    wxdiagram.persistence.save(loaded, second)

    first_json = json.loads(first.read_text())
    second_json = json.loads(second.read_text())
    assert first_json == second_json


def test_load_restores_connections_and_shapes(wx_app, tmp_path):
    diagram = make_diagram()
    path = tmp_path / "diagram.json"
    wxdiagram.persistence.save(diagram, path)

    loaded = wxdiagram.persistence.load(path)
    by_type = {}
    shapes = list(loaded.shapes)
    for shape in shapes:
        by_type.setdefault(type(shape).__name__, []).append(shape)

    assert len(by_type["RectangleShape"]) == 1
    assert len(by_type["Block"]) == 1
    assert len(by_type["DividedShape"]) == 1
    assert len(by_type["PolygonShape"]) == 1
    assert len(by_type["LineShape"]) == 1

    line = by_type["LineShape"][0]
    assert isinstance(line._from, RectangleShape)
    assert isinstance(line._to, Block)
    assert line._from is by_type["RectangleShape"][0]
    assert line._to is by_type["Block"][0]
    assert len(line._arcArrows) == 1
    assert line._arcArrows[0]._GetType() == ARROW_ARROW


def test_load_rejects_wrong_document(wx_app, tmp_path):
    path = tmp_path / "bogus.json"
    path.write_text(json.dumps({"app": "not-wxdiagram", "format_version": 1, "shapes": []}))
    with pytest.raises(ValueError):
        wxdiagram.persistence.load(path)


def test_connection_shape_round_trip(wx_app, tmp_path):
    diagram = Diagram()
    a = RectangleShape(0, 0, 50, 50)
    a._persist_id = 1
    b = RectangleShape(200, 200, 250, 250)
    b._persist_id = 2
    diagram.AppendShape(a)
    diagram.AppendShape(b)

    conn = ConnectionShape()
    conn.setInput(a, 0)
    conn.setOutput(b, 0)
    conn._persist_id = 3
    diagram.AppendShape(conn)

    path = tmp_path / "conn.json"
    wxdiagram.persistence.save(diagram, path)
    loaded = wxdiagram.persistence.load(path)
    lines = [s for s in loaded.shapes if isinstance(s, ConnectionShape)]
    assert len(lines) == 1
    line = lines[0]
    assert isinstance(line.input[0], RectangleShape)
    assert isinstance(line.output[0], RectangleShape)


def test_text_shape_round_trip(wx_app, tmp_path):
    diagram = Diagram()
    caption = wxdiagram.TextShape(10, 20, "Section heading", colour="RED")
    caption._persist_id = 1
    diagram.AppendShape(caption)

    path = tmp_path / "caption.json"
    wxdiagram.persistence.save(diagram, path)
    loaded = wxdiagram.persistence.load(path)
    loaded_caption = loaded.shapes[0]
    assert isinstance(loaded_caption, wxdiagram.TextShape)
    assert loaded_caption.label == "Section heading"
    assert loaded_caption.x == [10]
    assert loaded_caption.y == [20]
    assert loaded_caption.label_colour.Red() == 255


def test_composite_round_trip(wx_app, tmp_path):
    from wxdiagram.composite import CompositeShape

    diagram = Diagram()
    composite = CompositeShape()
    child = RectangleShape(0, 0, 40, 30)
    child._persist_id = 1
    composite.add_child(child)
    composite._persist_id = 2
    diagram.AppendShape(composite)

    path = tmp_path / "composite.json"
    wxdiagram.persistence.save(diagram, path)
    before = json.loads(path.read_text())

    loaded = wxdiagram.persistence.load(path)
    out = tmp_path / "composite2.json"
    wxdiagram.persistence.save(loaded, out)
    after = json.loads(out.read_text())
    assert before == after

    comp = [s for s in loaded.shapes if isinstance(s, CompositeShape)][0]
    assert len(comp.GetChildren()) == 1
    assert isinstance(comp.GetChildren()[0], RectangleShape)
