"""Minimal wxdiagram example - a window with one rectangle. Run me."""

import wx
import wxdiagram

app = wx.App(redirect=False)

frame = wx.Frame(None, title="wxdiagram minimal", size=(600, 400))
canvas = wxdiagram.ShapeCanvas(frame)
canvas.SetBackgroundColour(wx.WHITE)
canvas.SetDiagram(wxdiagram.Diagram())

shape = wxdiagram.RectangleShape(100, 100, 300, 200)
shape.AddText("hello world")
canvas.InsertShape(shape, 999)

frame.Show()
canvas.update_virtual_size()
app.MainLoop()
