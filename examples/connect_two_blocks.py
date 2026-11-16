"""Connect two blocks with an arrow line."""

import wx
import wxdiagram

app = wx.App(redirect=False)

frame = wx.Frame(None, title="wxdiagram - connect blocks", size=(700, 400))
canvas = wxdiagram.ShapeCanvas(frame)
canvas.SetBackgroundColour(wx.WHITE)
canvas.SetDiagram(wxdiagram.Diagram())

left = wxdiagram.Block()
left.label = "caller"
left.move_to(100, 150)

right = wxdiagram.Block()
right.label = "callee"
right.move_to(420, 150)

canvas.InsertShape(left, 999)
canvas.InsertShape(right, 999)

canvas.join_shapes(left, right)

frame.Show()
canvas.update_virtual_size()
app.MainLoop()
