"""Zoom and pan: zoom to fit everything, zoom towards the cursor."""

import wx
import wxdiagram

app = wx.App(redirect=False)

frame = wx.Frame(None, title="wxdiagram - zoom (Ctrl + wheel)", size=(800, 500))
canvas = wxdiagram.ShapeCanvas(frame)
canvas.SetBackgroundColour(wx.WHITE)
canvas.SetDiagram(wxdiagram.Diagram())

for x in range(3):
    block = wxdiagram.Block()
    block.label = f"box {x + 1}"
    block.move_to(100 + x * 260, 150)
    canvas.InsertShape(block, 999)

status = frame.CreateStatusBar()
status.SetStatusText("Ctrl+wheel or pinch = zoom | drag empty canvas = pan | Ctrl+0 = reset")

frame.Show()
canvas.ZoomToFit()
app.MainLoop()
