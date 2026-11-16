"""Save a diagram to JSON and load it back."""

import tempfile
import os

import wx
import wxdiagram

app = wx.App(redirect=False)

frame = wx.Frame(None, title="wxdiagram - save / load", size=(800, 500))
canvas = wxdiagram.ShapeCanvas(frame)
canvas.SetBackgroundColour(wx.WHITE)
canvas.SetDiagram(wxdiagram.Diagram())

block = wxdiagram.Block()
block.label = "persisted!"
block.move_to(120, 100)
canvas.InsertShape(block, 999)

# save
path = os.path.join(tempfile.mkdtemp(prefix="wxdiagram_example_"), "example_diagram.json")
wxdiagram.persistence.save(canvas.diagram, path)
print("saved", path)

# load into a fresh diagram
diagram = wxdiagram.persistence.load(path)
print("loaded", len(diagram.shapes), "shape(s)")
for shape in diagram.shapes:
    print(" -", type(shape).__name__, getattr(shape, "label", ""))

frame.SetSizer(wx.BoxSizer(wx.VERTICAL))
frame.Show()
canvas.ZoomToFit()
app.MainLoop()
