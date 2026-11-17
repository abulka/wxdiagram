# ---------------------------------------------------------------------------------------------
# wxdiagram demo - a showcase of the library's capabilities
#
# Run from the repo root:
#
#     uv run python -m wxdiagram.demo
#
# What is shown and what you can do:
#
#   * A preloaded sample diagram: UML class boxes with connections, a composite
#     with four children, a bitmap, a diamond, an ellipse, an arrowed line and a
#     clean polyline, each in its own labelled section.
#   * File, Edit, Add, Arrange and View menus - a kitchen-sink tour of the API.
#   * Add menu with every shape type, captions, bitmaps and image files.
#   * Edit menu: undo/redo, duplicate, delete, select all, deselect.
#   * Arrange menu: bring to front/forward, send backward/to back.
#   * View menu: zoom controls and a toggle for click-to-raise z-order.
#   * Right-click a shape for z-order, duplicate and delete; right-click empty
#     canvas for selection and zoom commands.
#   * Drag on empty canvas to marquee-select; Alt/Space/middle-drag pans.
#   * File menu: save and load the diagram as JSON.
#   * Delete key removes the selection.  Ctrl+C / Ctrl+V copy and paste it.
# ---------------------------------------------------------------------------------------------

from pathlib import Path

import wx

import wxdiagram
from wxdiagram.composite import CompositeShape
from wxdiagram.persistence import load, save


def _measure_dc():
    """A scratch DC used for measuring text extents without a visible window."""
    bitmap = wx.Bitmap(1, 1)
    dc = wx.MemoryDC(bitmap)
    return dc


def make_caption(x, y, text):
    """A selectable, movable section heading."""
    font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    return wxdiagram.SelectableTextShape(x, y, text, colour=wx.Colour(90, 90, 90), font=font)


def make_class_box(name, attributes, methods, left, top, width=230):
    """Return a DividedShape with a header region and a body region, like a UML class box.

    Regions are configured following the wx.lib.ogl pattern: raw SetText,
    proportions, format modes, then FormatText() with a measuring DC so the
    library can lay text out by itself.
    """
    padding = 30
    body_lines = len(attributes) + len(methods)
    height = padding + 30 + body_lines * 22

    box = wxdiagram.DividedShape(width, height)

    header = wxdiagram.ShapeRegion()
    header.SetText(name)
    header.SetProportions(0.0, 0.22)
    header.SetFormatMode(wxdiagram.FORMAT_CENTRE_HORIZ | wxdiagram.FORMAT_CENTRE_VERT)
    header.SetFont(wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    box.AddRegion(header)

    body = wxdiagram.ShapeRegion()
    body.SetText("\n".join(attributes + ["────────────"] + methods))
    body.SetProportions(0.0, 0.78)
    body.SetFormatMode(wxdiagram.FORMAT_NONE)
    body.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    box.AddRegion(body)

    box.SetRegionSizes()

    dc = _measure_dc()
    try:
        for i, region in enumerate(box.GetRegions()):
            box.FormatText(dc, region.GetText(), i)
    finally:
        dc.SelectObject(wx.NullBitmap)

    box.move_to(left, top)
    return box


def make_diamond(left, top):
    w, h = 140, 90
    diamond = wxdiagram.PolygonShape()
    diamond.Create([(0, -h / 2), (w / 2, 0), (0, h / 2), (-w / 2, 0)])
    diamond.move_to(left, top)
    return diamond


def make_polyline(left, top):
    # A deliberately simple three-point polyline: clean, not a scribble.
    points = [(0, 40), (120, 0), (240, 40)]
    line = wxdiagram.LinesShape(points)
    line.move_to(left, top)
    return line


SAMPLE_IMAGE = Path(__file__).resolve().parent.parent / "examples" / "assets" / "sample-image.jpg"


def make_bitmap_shape(left, top):
    """A resizable bitmap, using the sample image when available."""
    shape = wxdiagram.ResizableBitmapShape()
    if SAMPLE_IMAGE.exists():
        image = wx.Image(str(SAMPLE_IMAGE), wx.BITMAP_TYPE_ANY)
        if image.IsOk():
            width, height = image.GetWidth(), image.GetHeight()
            max_w, max_h = 220, 180
            scale = min(1.0, max_w / width, max_h / height)
            if scale < 0.999:
                image = image.Scale(
                    max(1, int(width * scale)),
                    max(1, int(height * scale)),
                    wx.IMAGE_QUALITY_HIGH,
                )
            shape.SetBitmap(wx.Bitmap(image))
            shape.SetFilename(str(SAMPLE_IMAGE))
            shape.move_to(left, top)
            return shape

    # Fallback when running from an installed wheel without the examples tree.
    size = wx.Size(160, 110)
    image = wx.Image(size)
    for row in range(size.height):
        for col in range(size.width):
            r = int(70 + 150 * row / size.height)
            g = int(120 + 70 * (1 - col / size.width))
            b = 200 - int(70 * row / size.height)
            image.SetRGB(col, row, r, g, b)
    shape.SetBitmap(wx.Bitmap(image))
    shape.move_to(left, top)
    return shape


def make_composite(left, top):
    """One composite holding four children in a neatly aligned 2x2 grid."""
    box_w, box_h, gap = 130, 60, 20
    comp = CompositeShape()

    for i, label in enumerate(("Item A", "Item B", "Item C", "Item D")):
        column, row = i % 2, i // 2
        child_left = 10 + column * (box_w + gap)
        child_top = 10 + row * (box_h + gap)
        child = wxdiagram.Block()
        child.x = [child_left, child_left + box_w]
        child.y = [child_top, child_top + box_h]
        child.label = label
        child.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        comp.add_child(child)

    comp.CalculateSize()
    # a little breathing room between the children and the composite frame
    comp.x = [comp.x[0] - 10, comp.x[1] + 10]
    comp.y = [comp.y[0] - 10, comp.y[1] + 10]
    comp.move_to(left, top)
    return comp


def _populate(canvas):
    shapes = []
    captions = []

    # -- UML classes and connections -------------------------------------------------
    captions.append(make_caption(30, 20, "UML CLASSES & CONNECTIONS"))

    client = wxdiagram.Block()
    client.label = "Client"
    client.x = [30, 170]
    client.y = [70, 140]

    controller = make_class_box(
        "UserController",
        ["+ user_service: UserService"],
        ["+ get(name): User", "+ post(req): Response"],
        300,
        40,
    )

    service = make_class_box(
        "UserService",
        ["# cache: Cache"],
        ["+ find_user(id): User", "+ save_user(u)"],
        300,
        280,
    )

    shapes.extend([client, controller, service])

    # -- composite --------------------------------------------------------------------
    captions.append(make_caption(620, 20, "COMPOSITE (2x2 GRID)"))
    composite = make_composite(620, 50)
    shapes.append(composite)

    # -- basic shapes -----------------------------------------------------------------
    captions.append(make_caption(620, 260, "BASIC SHAPES"))
    rectangle = wxdiagram.ResizableRectangleShape(620, 300, 740, 370)
    rectangle.SetBrush(wx.Brush("LIGHT BLUE"))
    ellipse = wxdiagram.ConnectableEllipseShape()
    ellipse.x = [760, 880]
    ellipse.y = [300, 370]
    ellipse.SetBrush(wx.Brush("PALE GREEN"))
    diamond = make_diamond(960, 300)
    diamond.SetBrush(wx.Brush("LIGHT YELLOW"))
    shapes.extend([rectangle, ellipse, diamond])

    # -- media and code ---------------------------------------------------------------
    captions.append(make_caption(620, 410, "MEDIA & CODE"))
    bitmap = make_bitmap_shape(620, 450)
    shapes.append(bitmap)

    # -- edge styles: the same pair connected five ways ------------------------
    captions.append(make_caption(50, 420, "EDGE STYLES"))

    def edge_pair(top, right_top, label, mode, colour, blocker=False, label_offset=-18):
        left = wxdiagram.RectangleShape(50, top, 160, top + 60)
        right = wxdiagram.RectangleShape(280, right_top, 390, right_top + 60)
        for box in (left, right):
            box.SetBrush(wx.Brush(colour))
        shapes.extend([left, right])
        if blocker:
            bar = wxdiagram.RectangleShape(200, top + 22, 245, top + 40)
            bar.SetBrush(wx.Brush("LIGHT GREY"))
            shapes.append(bar)
        edge = canvas.join_shapes(left, right)
        edge.SetRouteMode(mode)
        edge.AddText(label)
        edge.SetLabelPosition(0, 0, label_offset)  # keep the label off the line

    edge_pair(450, 450, "straight", "straight", "LIGHT BLUE")
    edge_pair(530, 530, "curved", "curved", "PALE GREEN")
    edge_pair(610, 610, "auto", "auto", "PALE GREEN", blocker=True, label_offset=-26)
    edge_pair(690, 690, "avoid", "avoid", "PALE GREEN", blocker=True, label_offset=-26)
    edge_pair(810, 790, "orthogonal", "orthogonal", "LIGHT YELLOW", label_offset=30)

    # -- lines and arrows -------------------------------------------------------------
    captions.append(make_caption(880, 410, "LINES & ARROWS"))
    polyline = make_polyline(880, 445)
    arrowed = wxdiagram.LineShape()
    arrowed.MakeLineControlPoints(2)
    arrowed.SetEnds(880, 490, 1110, 540)
    arrowed._pen = wx.Pen(wx.BLACK, 2, wx.PENSTYLE_LONG_DASH)
    arrowed.AddArrow(wxdiagram.ARROW_ARROW, wxdiagram.ARROW_POSITION_END, size=12.0)
    shapes.extend([polyline, arrowed])

    # A spline (bezier-like smooth curve) through three control points.
    spline = wxdiagram.LineShape()
    spline.MakeLineControlPoints(3)
    spline._lineControlPoints[0] = wx.RealPoint(880, 580)
    spline._lineControlPoints[1] = wx.RealPoint(995, 620)
    spline._lineControlPoints[2] = wx.RealPoint(1110, 580)
    spline.SetSpline(True)
    spline.AddArrow(wxdiagram.ARROW_ARROW, wxdiagram.ARROW_POSITION_END, size=12.0)
    spline.AddText("spline")
    spline.SetLabelPosition(0, 0, -16)
    shapes.append(spline)

    # One line showing the different arrow kinds and positions it can carry.
    arrows = wxdiagram.LineShape()
    arrows.MakeLineControlPoints(2)
    arrows.SetEnds(880, 660, 1110, 660)
    arrows.AddArrow(
        wxdiagram.ARROW_DOUBLE_OBLIQUE, wxdiagram.ARROW_POSITION_START, size=12.0
    )
    arrows.AddArrow(wxdiagram.ARROW_ARROW, wxdiagram.ARROW_POSITION_MIDDLE, size=10.0)
    arrows.AddArrow(
        wxdiagram.ARROW_FILLED_CIRCLE, wxdiagram.ARROW_POSITION_END, size=10.0
    )
    arrows.AddText("arrow types")
    arrows.SetLabelPosition(0, 0, -16)
    shapes.append(arrows)

    # A bent line: one control point per bend, editable with the resize nodes.
    bent = wxdiagram.LineShape()
    bent.MakeLineControlPoints(4)
    bent._lineControlPoints[0] = wx.RealPoint(880, 710)
    bent._lineControlPoints[1] = wx.RealPoint(960, 680)
    bent._lineControlPoints[2] = wx.RealPoint(1030, 740)
    bent._lineControlPoints[3] = wx.RealPoint(1110, 700)
    bent.AddArrow(wxdiagram.ARROW_ARROW, wxdiagram.ARROW_POSITION_END, size=12.0)
    bent.AddText("bend points")
    bent.SetLabelPosition(0, 0, -16)
    shapes.append(bent)

    # -- connections: attached lines, routed via the box perimeters ---------------
    uses = canvas.join_shapes(client, controller)
    if uses is not None:
        uses.SetRouteMode("auto")
        uses.AddText("uses")
    # vertical relationship: controller bottom -> service top
    delegates = canvas.join_shapes(controller, service)
    if delegates is not None:
        delegates.SetRouteMode("auto")
        delegates.AddText("delegates")

    for caption in captions:
        canvas.InsertShape(caption, 999)
    for shape in shapes:
        canvas.InsertShape(shape, 999)
    # Route once everything is in the diagram, so edges can see the obstacles
    # (the shapes above were created before being inserted).
    for shape in canvas.diagram.shapes:
        if isinstance(shape, wxdiagram.LineShape) and shape.autoRoute:
            shape.UpdateRoute()


class DemoFrame(wx.Frame):
    def __init__(self):
        super().__init__(
            None,
            title="wxdiagram demo - a faster, zoomable diagramming library for wxPython",
            size=(1200, 760),
        )
        self.Centre()

        self.canvas = wxdiagram.ShapeCanvas(self)
        self.canvas.SetBackgroundColour(wx.WHITE)
        self.canvas.SetDiagram(wxdiagram.Diagram())
        self.canvas.Bind(wx.EVT_RIGHT_UP, self.OnCanvasRightClick)

        self._create_menus()
        self.CreateStatusBar()
        self.SetStatusText(
            "Drag empty = marquee | Shift/Ctrl add | Alt/Space/middle drag = pan | "
            "Corner resize = proportional (Shift = free, Alt = centre) | "
            "Ctrl+wheel zoom | "
            "Ctrl+Z undo | Ctrl+D duplicate | Del delete"
        )

        _populate(self.canvas)
        self.canvas.ZoomToFit()

    def _menu(self, title):
        menu = wx.Menu()
        if not hasattr(self, "_menu_bar"):
            self._menu_bar = wx.MenuBar()
            self.SetMenuBar(self._menu_bar)
        self._menu_bar.Append(menu, title)
        return menu

    def _add_item(self, menu, label, handler, help_text=""):
        item = wx.MenuItem(menu, wx.ID_ANY, label, help_text)
        menu.Append(item)
        self.Bind(wx.EVT_MENU, handler, id=item.GetId())

    def _create_menus(self):
        file_menu = self._menu("&File")
        self._add_item(file_menu, "&New\tCtrl+N", self.OnNew, "Clear the diagram")
        self._add_item(file_menu, "&Open...\tCtrl+O", self.OnOpen, "Load a JSON diagram")
        self._add_item(file_menu, "&Save\tCtrl+S", self.OnSave, "Save as JSON")
        self._add_item(file_menu, "Save &As...\tCtrl+Shift+S", self.OnSave, "Save as JSON")
        self._add_item(
            file_menu, "Export &PNG...\tCtrl+Shift+E", self.OnExportPng, "Save a PNG image"
        )
        self._add_item(file_menu, "E&xit\tAlt+F4", self.OnExit, "Quit")

        edit_menu = self._menu("&Edit")
        self._add_item(edit_menu, "&Undo\tCtrl+Z", lambda e: self.canvas.undo())
        self._add_item(edit_menu, "&Redo\tCtrl+Shift+Z", lambda e: self.canvas.redo())
        self._add_item(edit_menu, "&Duplicate\tCtrl+D", lambda e: self.canvas.duplicate_selected())
        self._add_item(edit_menu, "&Delete\tDel", lambda e: self.canvas.delete_selected())
        edit_menu.AppendSeparator()
        self._add_item(edit_menu, "Select &All\tCtrl+A", self.OnSelectAll)
        self._add_item(edit_menu, "&Deselect\tEsc", lambda e: self.canvas.deselect())

        add_menu = self._menu("&Add")
        self._add_item(
            add_menu,
            "&Rectangle\tCtrl+R",
            lambda e: self._add_shape(wxdiagram.ResizableRectangleShape(0, 0, 120, 80)),
            "ResizableRectangleShape",
        )
        self._add_item(
            add_menu,
            "&Ellipse\tCtrl+E",
            lambda e: self._add_shape(wxdiagram.ConnectableEllipseShape()),
            "EllipseShape",
        )
        self._add_item(
            add_menu,
            "&Block\tCtrl+B",
            lambda e: self._add_shape(wxdiagram.Block()),
            "Labelled block",
        )
        self._add_item(
            add_menu,
            "Di&vided (UML class)\tCtrl+D",
            lambda e: self._add_shape(
                make_class_box("Class", ["+ attribute"], ["+ method()"], 0, 0)
            ),
            "DividedShape",
        )
        self._add_item(
            add_menu,
            "&Polygon\tCtrl+P",
            lambda e: self._add_shape(make_diamond(300, 300)),
            "PolygonShape",
        )
        self._add_item(
            add_menu,
            "&Composite\tCtrl+M",
            lambda e: self._add_shape(make_composite(300, 300)),
            "CompositeShape",
        )
        self._add_item(
            add_menu,
            "&Text caption",
            lambda e: self._add_shape(make_caption(300, 500, "A caption")),
            "SelectableTextShape - movable caption",
        )
        self._add_item(
            add_menu,
            "Sample &Bitmap",
            lambda e: self._add_shape(make_bitmap_shape(300, 300)),
            "ResizableBitmapShape from examples/assets",
        )
        self._add_item(add_menu, "&Image from file...", self.OnAddImage, "ResizableBitmapShape")
        self._add_item(
            add_menu,
            "&Connect two selected\tCtrl+J",
            self.OnConnect,
            "Draw a line between the two selected shapes",
        )

        arrange_menu = self._menu("&Arrange")
        self._add_item(arrange_menu, "Bring to &Front", lambda e: self.canvas.bring_to_front())
        self._add_item(arrange_menu, "Bring F&orward", lambda e: self.canvas.bring_forward())
        self._add_item(arrange_menu, "Send Back&ward", lambda e: self.canvas.send_backward())
        self._add_item(arrange_menu, "Send to &Back", lambda e: self.canvas.send_to_back())

        view_menu = self._menu("&View")
        self.item_raise = view_menu.AppendCheckItem(
            wx.ID_ANY, "Raise clicked shape", "Change z-order when a shape is clicked"
        )
        self.item_raise.Check(self.canvas.bringClickedShapeToFront)
        self.Bind(wx.EVT_MENU, self.OnToggleRaiseClicked, self.item_raise)
        self.item_grid = view_menu.AppendCheckItem(wx.ID_ANY, "Show &grid", "Draw the diagram grid")
        self.item_grid.Check(self.canvas.showGrid)
        self.Bind(wx.EVT_MENU, self.OnToggleGrid, self.item_grid)
        self.item_snap = view_menu.AppendCheckItem(
            wx.ID_ANY, "&Snap to grid", "Snap shape drags to the grid"
        )
        self.item_snap.Check(self.canvas.snapToGrid)
        self.Bind(wx.EVT_MENU, self.OnToggleSnap, self.item_snap)
        self.item_guides = view_menu.AppendCheckItem(
            wx.ID_ANY, "Alignment &guides", "Snap to other shapes' edges and centres"
        )
        self.item_guides.Check(self.canvas.alignmentGuides)
        self.Bind(wx.EVT_MENU, self.OnToggleGuides, self.item_guides)
        view_menu.AppendSeparator()
        self._add_item(
            view_menu,
            "Zoom &In\tCtrl+=",
            lambda e: self.canvas.ZoomIn(anchor="center"),
            "Ctrl + mouse wheel also works",
        )
        self._add_item(
            view_menu,
            "Zoom &Out\tCtrl+-",
            lambda e: self.canvas.ZoomOut(anchor="center"),
            "Ctrl + mouse wheel also works",
        )
        self._add_item(
            view_menu,
            "Zoom to &Fit\tCtrl+F",
            lambda e: self.canvas.ZoomToFit(),
            "Fit everything on screen",
        )
        self._add_item(
            view_menu, "R&eset Zoom\tCtrl+0", lambda e: self.canvas.ZoomReset(), "Back to 100%"
        )

    def _add_shape(self, shape):
        self.canvas.InsertShape(shape, 999)
        self.canvas.deselect()
        if getattr(shape, "marqueeSelectable", True):
            self.canvas.select(shape)
        self.canvas.update_virtual_size()
        self.canvas.Refresh()  # paint the new shape immediately

    def OnCanvasRightClick(self, event):
        shape = self.canvas.getCurrentShape(event)
        if hasattr(shape, "item"):  # right-clicked on a resize handle
            shape = shape.item
        if shape is not None:
            if shape not in self.canvas.getSelectedShapes():
                self.canvas.deselect()
                self.canvas.select(shape)
            menu = self._shape_menu(shape)
        else:
            menu = self._canvas_menu()
        self._show_popup(menu, event.GetPosition())

    def _show_popup(self, menu, position):
        try:
            self.canvas.PopupMenu(menu, position)
        finally:
            menu.Destroy()

    def _canvas_menu(self):
        menu = wx.Menu()
        self._popup_item(menu, "Select All", lambda e: self.OnSelectAll(e))
        self._popup_item(menu, "Deselect", lambda e: self.canvas.deselect())
        menu.AppendSeparator()
        self._popup_item(menu, "Zoom In", lambda e: self.canvas.ZoomIn(anchor="center"))
        self._popup_item(menu, "Zoom Out", lambda e: self.canvas.ZoomOut(anchor="center"))
        self._popup_item(menu, "Zoom to Fit", lambda e: self.canvas.ZoomToFit())
        self._popup_item(menu, "Reset Zoom", lambda e: self.canvas.ZoomReset())
        return menu

    def _shape_menu(self, shape):
        menu = wx.Menu()
        self._popup_item(menu, "Bring to Front", lambda e: self.canvas.bring_to_front())
        self._popup_item(menu, "Bring Forward", lambda e: self.canvas.bring_forward())
        self._popup_item(menu, "Send Backward", lambda e: self.canvas.send_backward())
        self._popup_item(menu, "Send to Back", lambda e: self.canvas.send_to_back())
        menu.AppendSeparator()
        self._popup_item(menu, "Duplicate", lambda e: self.canvas.duplicate_selected())
        self._popup_item(menu, "Delete", lambda e: self.canvas.delete_selected())
        if isinstance(shape, wxdiagram.LineShape) and getattr(shape, "_from", None) is not None:
            menu.AppendSeparator()
            current = shape.GetRouteMode()
            for label, mode in (
                ("Edge: &Straight", "straight"),
                ("Edge: &Curved", "curved"),
                ("Edge: &Auto (straight or curved)", "auto"),
                ("Edge: &Avoid boxes", "avoid"),
                ("Edge: &Orthogonal", "orthogonal"),
            ):
                item = menu.AppendRadioItem(wx.ID_ANY, label)
                item.Check(current == mode)
                self.Bind(
                    wx.EVT_MENU,
                    lambda e, s=shape, m=mode: self._set_route_mode(s, m),
                    item,
                )
        if hasattr(shape, "ResetSize"):
            menu.AppendSeparator()
            self._popup_item(menu, "Reset Image Size", lambda e: self._reset_image_size(shape))
        return menu

    def _popup_item(self, menu, label, handler):
        item = menu.Append(wx.ID_ANY, label)
        self.Bind(wx.EVT_MENU, handler, item)

    def _set_route_mode(self, shape, mode):
        shape.SetRouteMode(mode)
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def _reset_image_size(self, shape):
        shape.ResetSize()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def OnSelectAll(self, event):
        self.canvas.deselect()
        for shape in self.canvas.GetDiagram().shapes:
            if getattr(shape, "marqueeSelectable", True):
                self.canvas.select(shape)

    def OnAddImage(self, event):
        with wx.FileDialog(
            self,
            "Insert image",
            wildcard="Images|*.png;*.jpg;*.jpeg;*.bmp;*.gif|All files|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            shape = self.canvas.AddImage(
                dlg.GetPath(), max_size=(500, 400), center=True, send_to_back=False
            )
            if shape is not None:
                self.canvas.deselect()
                self.canvas.select(shape)
                self.canvas.Refresh()

    def OnToggleRaiseClicked(self, event):
        self.canvas.bringClickedShapeToFront = self.item_raise.IsChecked()

    def OnToggleGrid(self, event):
        self.canvas.showGrid = self.item_grid.IsChecked()
        self.canvas.Refresh()

    def OnToggleSnap(self, event):
        self.canvas.snapToGrid = self.item_snap.IsChecked()

    def OnToggleGuides(self, event):
        self.canvas.alignmentGuides = self.item_guides.IsChecked()

    def OnConnect(self, event):
        selected = self.canvas.getSelectedShapes()
        if len(selected) == 2:
            self.canvas.join_shapes(selected[0], selected[1])
            self.canvas.deselect()
            self.canvas.Refresh()
        else:
            wx.MessageBox(
                "Select two shapes first, then Add > Connect two selected",
                "wxdiagram demo",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )

    def OnNew(self, event):
        self.canvas.SetDiagram(wxdiagram.Diagram())
        self.canvas.deselect()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def OnOpen(self, event):
        with wx.FileDialog(
            self,
            "Open diagram",
            wildcard="wxdiagram JSON (*.json)|*.json|All files|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            try:
                diagram = load(dlg.GetPath())
            except Exception as e:  # noqa: BLE001 - surface the problem to the user
                wx.MessageBox(
                    f"Could not load:\n{e}", "wxdiagram demo", wx.OK | wx.ICON_ERROR, self
                )
                return
            self.canvas.SetDiagram(diagram)
            self.canvas.deselect()
            self.canvas.update_virtual_size()
            self.canvas.ZoomToFit()

    def OnSave(self, event):
        with wx.FileDialog(
            self,
            "Save diagram as...",
            wildcard="wxdiagram JSON (*.json)|*.json",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()
            if not path.lower().endswith(".json"):
                path += ".json"
            save(self.canvas.diagram, path)
            self.SetStatusText(f"Saved {path}")

    def OnExportPng(self, event):
        with wx.FileDialog(
            self,
            "Export PNG",
            wildcard="PNG image (*.png)|*.png",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()
            if not path.lower().endswith(".png"):
                path += ".png"
            if self.canvas.ExportPng(path, margin=10):
                self.SetStatusText(f"Exported {path}")
            else:
                wx.MessageBox(
                    f"Could not write {path}", "wxdiagram demo", wx.OK | wx.ICON_ERROR, self
                )

    def OnExit(self, event):
        self.Close()


def main():
    app = wx.App(redirect=False)
    frame = DemoFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
