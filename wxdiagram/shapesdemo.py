# ---------------------------------------------------------------------------------------------
# wxdiagram shapesdemo - a Shape Studio-style shape editor built on wxdiagram
#
# Run from the repo root:
#
#     uv run python -m wxdiagram.shapesdemo
#
# What is shown and what you can do:
#
#   * Add rectangles, circles, ellipses, triangles and free lines to the canvas.
#   * A resizable properties panel on the right edits name, position, size,
#     fill/border colours and border width; attached edges expose route mode,
#     arrowheads and endpoints.
#   * Shapes resize from four corner handles; connect from four round side
#     dots.  Releasing a connection over another shape's body creates an
#     attached edge that follows both shapes when they move.
#   * Group/ungroup, duplicate, z-order, undo/redo, marquee selection,
#     grid/snap/alignment guides, zoom controls and a status bar.
#   * Resizable, wrapping properties panel that stays readable at narrow
#     widths, and light/dark/system themes (View > Theme).
#   * File menu: save/load the diagram as JSON, export PNG.
#   * Right-click a shape for z-order, duplicate, delete and group commands;
#     right-click empty canvas for add/select/zoom commands.
# ---------------------------------------------------------------------------------------------

import wx

import wxdiagram
from wxdiagram.composite import GroupShape
from wxdiagram.core import CircleShape
from wxdiagram.lines import LineShape
from wxdiagram.persistence import load, save


# -- demo shape kinds ---------------------------------------------------------------

PALETTE = {
    "Rectangle": "#4C8DFF",
    "Circle": "#FFA94D",
    "Ellipse": "#3ED3A5",
    "Triangle": "#4C8DFF",
    "Line": "#FFA94D",
}

DEFAULT_SIZES = {
    "Rectangle": (230, 120),
    "Circle": (140, 140),
    "Ellipse": (160, 120),
    "Triangle": (170, 140),
    "Line": (220, 110),
}


# -- theming ------------------------------------------------------------------------

LIGHT_THEME = {
    "window_bg": wx.Colour(216, 220, 230),
    "panel_bg": wx.Colour(228, 231, 239),
    "panel_body_bg": wx.Colour(238, 240, 246),
    "card_bg": wx.Colour(219, 223, 233),
    "field_bg": wx.Colour(255, 255, 255),
    "text": wx.Colour(30, 34, 48),
    "muted": wx.Colour(90, 98, 114),
    "border": wx.Colour(188, 193, 206),
    "button_bg": wx.Colour(216, 220, 230),
    "button_hover": wx.Colour(204, 209, 221),
    "button_pressed": wx.Colour(191, 197, 211),
    "button_text": wx.Colour(30, 34, 48),
    "danger": wx.Colour(184, 58, 58),
    "canvas_bg": wx.Colour(253, 253, 254),
    "grid": wx.Colour(232, 233, 238),
    "guide": wx.Colour(192, 63, 192),
    "handle_fill": wx.Colour(32, 36, 44),
    "handle_outline": wx.Colour(255, 255, 255),
    "port_fill": wx.Colour(255, 255, 255),
    "port_outline": wx.Colour(75, 81, 96),
    "marquee": wx.Colour(63, 109, 255),
    "sash_bg": wx.Colour(198, 203, 216),
    "sash_line": wx.Colour(145, 152, 168),
    "connection": wx.Colour(63, 109, 255),
    "edge": wx.Colour(47, 52, 66),
}

DARK_THEME = {
    "window_bg": wx.Colour(23, 24, 27),
    "panel_bg": wx.Colour(42, 43, 48),
    "panel_body_bg": wx.Colour(35, 36, 41),
    "card_bg": wx.Colour(52, 53, 60),
    "field_bg": wx.Colour(29, 30, 34),
    "text": wx.Colour(236, 236, 241),
    "muted": wx.Colour(160, 163, 173),
    "border": wx.Colour(74, 76, 85),
    "button_bg": wx.Colour(59, 60, 68),
    "button_hover": wx.Colour(71, 73, 84),
    "button_pressed": wx.Colour(83, 85, 98),
    "button_text": wx.Colour(236, 236, 241),
    "danger": wx.Colour(240, 122, 122),
    "canvas_bg": wx.Colour(27, 28, 31),
    "grid": wx.Colour(46, 47, 53),
    "guide": wx.Colour(217, 119, 217),
    "handle_fill": wx.Colour(240, 240, 244),
    "handle_outline": wx.Colour(27, 28, 31),
    "port_fill": wx.Colour(240, 240, 244),
    "port_outline": wx.Colour(17, 18, 22),
    "marquee": wx.Colour(143, 179, 255),
    "sash_bg": wx.Colour(52, 53, 60),
    "sash_line": wx.Colour(91, 94, 105),
    "connection": wx.Colour(143, 179, 255),
    "edge": wx.Colour(215, 217, 226),
}

THEMES = {"light": LIGHT_THEME, "dark": DARK_THEME}


def resolve_theme(name):
    """Return a palette for ``system``, ``light`` or ``dark``."""
    if name in THEMES:
        return THEMES[name]
    try:
        dark = wx.SystemSettings.GetAppearance().IsDark()
    except Exception:  # noqa: BLE001 - older wxWidgets / non-mac platforms
        dark = False
    return THEMES["dark" if dark else "light"]


class WrappingLabel(wx.StaticText):
    """A static label that re-wraps its text when the panel is resized."""

    def __init__(self, parent, text="", colour=None, margin=0):
        super().__init__(parent, label=text)
        self._base_text = text
        self._wrap_width = None
        self._margin = margin
        if colour is not None:
            self.SetForegroundColour(colour)

    def set_text(self, text):
        self._base_text = text
        if self._wrap_width:
            self._apply_wrap()
        else:
            self.SetLabel(text)

    def wrap_to(self, width):
        self._wrap_width = max(80, int(width) - self._margin)
        self._apply_wrap()

    def _apply_wrap(self):
        # wx.StaticText.Wrap() refuses to re-wrap when the target width is
        # close to the control's current width on macOS, which left long
        # labels clipped.  Word-wrap explicitly so the result is predictable.
        if not self._wrap_width:
            return
        dc = wx.MemoryDC(wx.Bitmap(1, 1))
        try:
            dc.SetFont(self.GetFont())
            lines = []
            for paragraph in self._base_text.split("\n"):
                words = paragraph.split()
                if not words:
                    lines.append("")
                    continue
                current = words[0]
                for word in words[1:]:
                    candidate = f"{current} {word}"
                    if dc.GetTextExtent(candidate)[0] <= self._wrap_width:
                        current = candidate
                    else:
                        lines.append(current)
                        current = word
                lines.append(current)
            self.SetLabel("\n".join(lines))
        finally:
            dc.SelectObject(wx.NullBitmap)


class FlatButton(wx.Control):
    """A small owner-drawn button that follows the palette and centres its label."""

    def __init__(self, parent, label, palette, on_click=None, danger=False, height=32):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._label = label
        self._palette = palette
        self._on_click = on_click
        self._danger = danger
        self._hover = False
        self._pressed = False
        self._height = height
        self.SetMinSize((-1, height))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_down)
        self.Bind(wx.EVT_LEFT_UP, self._on_up)
        self.Bind(wx.EVT_SIZE, self._on_size)

    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        palette = self._palette
        dc.SetBackground(wx.Brush(palette["panel_bg"]))
        dc.Clear()
        if self._pressed:
            background = palette["button_pressed"]
        elif self._hover:
            background = palette["button_hover"]
        else:
            background = palette["button_bg"]
        width, height = self.GetClientSize()
        dc.SetPen(wx.Pen(palette["border"], 1))
        dc.SetBrush(wx.Brush(background))
        dc.DrawRoundedRectangle(0, 0, width, height, 7)
        dc.SetFont(self.GetFont())
        dc.SetTextForeground(palette["danger"] if self._danger else palette["button_text"])
        text_width, text_height = dc.GetTextExtent(self._label)
        dc.DrawText(
            self._label,
            max(6, int((width - text_width) / 2)),
            int((height - text_height) / 2),
        )

    def _on_size(self, event):
        self.Refresh()
        event.Skip()

    def _on_enter(self, event):
        self._hover = True
        self.Refresh()
        event.Skip()

    def _on_leave(self, event):
        self._hover = False
        self._pressed = False
        self.Refresh()
        event.Skip()

    def _on_down(self, event):
        self._pressed = True
        self.Refresh()
        event.Skip()

    def _on_up(self, event):
        self._pressed = False
        inside = self.GetClientRect().Contains(event.GetPosition())
        self.Refresh()
        if inside and self._on_click is not None:
            self._on_click(None)
        event.Skip()


class DemoRect(
    wxdiagram.RectangleShape,
    wxdiagram.Connectable,
    wxdiagram.Resizeable,
    wxdiagram.Selectable,
    wxdiagram.Attributable,
):
    """A connectable, resizable rectangle (no label dialog on Ctrl+click)."""

    def __init__(self, left=20, top=20, right=140, bottom=100):
        wxdiagram.RectangleShape.__init__(self, left, top, right, bottom)
        wxdiagram.Connectable.__init__(self)
        wxdiagram.Attributable.__init__(self)
        self.label = ""


class DemoTriangle(wxdiagram.PolygonShape, wxdiagram.Connectable, wxdiagram.Selectable):
    """A connectable, resizable triangle whose ports use the real perimeter."""

    def __init__(self, points=()):
        wxdiagram.PolygonShape.__init__(self)
        wxdiagram.Connectable.__init__(self)
        if points:
            self.Create(list(points))


class DemoLine(wxdiagram.LinesShape, wxdiagram.Selectable):
    """A free two-point line (an unattached polyline, not an edge)."""

    def __init__(self, points):
        wxdiagram.LinesShape.__init__(self, list(points))


# Demo-local classes must round-trip through JSON: register them alongside the
# library defaults so save/load works from this module.
wxdiagram.persistence.register_shape_class(DemoRect)
wxdiagram.persistence.register_shape_class(DemoTriangle)
wxdiagram.persistence.register_shape_class(DemoLine)


def _is_attached_edge(shape):
    return isinstance(shape, LineShape) and (
        getattr(shape, "_from", None) is not None or getattr(shape, "_to", None) is not None
    )


def _is_free_line(shape):
    return isinstance(shape, wxdiagram.LinesShape) and not isinstance(
        shape, (LineShape, wxdiagram.PolygonShape)
    )


def _bbox_of(shape):
    return min(shape.x), min(shape.y), max(shape.x), max(shape.y)


def _kind_name(shape):
    if isinstance(shape, GroupShape):
        return "Group"
    if isinstance(shape, CircleShape):
        return "Circle"
    if isinstance(shape, DemoTriangle):
        return "Triangle"
    if _is_attached_edge(shape):
        return "Edge"
    if _is_free_line(shape):
        return "Line"
    if isinstance(shape, wxdiagram.ConnectableEllipseShape):
        return "Ellipse"
    if isinstance(shape, wxdiagram.RectangleShape):
        return "Rectangle"
    return type(shape).__name__


# -- properties panel ---------------------------------------------------------------

PANEL_WIDTH = 320


class SashHandle(wx.Panel):
    """A wide, visible drag handle for the properties pane.

    macOS exposes only a 1 px splitter sash, which is almost impossible to
    grab.  This strip lives just inside the panel and moves the splitter sash
    as the pointer is dragged.
    """

    WIDTH = 12

    def __init__(self, parent, frame, palette):
        super().__init__(parent, size=(self.WIDTH, -1))
        self.frame = frame
        self.palette = palette
        self._dragging = False
        self._start_mouse_x = 0
        self._start_sash = 0
        self.SetMinSize((self.WIDTH, -1))
        self.SetMaxSize((self.WIDTH, -1))
        self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_down)
        self.Bind(wx.EVT_LEFT_UP, self._on_up)
        self.Bind(wx.EVT_MOTION, self._on_motion)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self._on_capture_lost)

    def set_palette(self, palette):
        self.palette = palette
        self.Refresh()

    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        width, height = self.GetClientSize()
        dc.SetBackground(wx.Brush(self.palette["sash_bg"]))
        dc.Clear()
        line = self.palette["sash_line"]
        dc.SetPen(wx.Pen(line, 1))
        dc.DrawLine(width // 2, 0, width // 2, height)
        grip_pen = wx.Pen(line, 2)
        dc.SetPen(grip_pen)
        centre_x = width // 2
        centre_y = height // 2
        for offset in (-7, 0, 7):
            dc.DrawLine(centre_x - 2, centre_y + offset, centre_x + 2, centre_y + offset)

    def _on_down(self, event):
        self._dragging = True
        self._start_mouse_x = wx.GetMousePosition().x
        self._start_sash = self.frame.splitter.GetSashPosition()
        if not self.HasCapture():
            self.CaptureMouse()
        self.Refresh()
        event.Skip()

    def _on_up(self, event):
        self._dragging = False
        if self.HasCapture():
            self.ReleaseMouse()
        self.Refresh()
        event.Skip()

    def _on_motion(self, event):
        if not self._dragging or not event.Dragging():
            event.Skip()
            return
        splitter = self.frame.splitter
        delta = wx.GetMousePosition().x - self._start_mouse_x
        total = splitter.GetClientSize().width
        new_sash = max(260, min(total - 260, self._start_sash + delta))
        splitter.SetSashPosition(new_sash)
        self.frame.panel._relayout()
        event.Skip()

    def _on_capture_lost(self, event):
        self._dragging = False
        self.Refresh()
        event.Skip()


class PropertiesPanel(wx.Panel):
    """Right-hand inspector bound to the canvas selection."""

    def __init__(self, parent, canvas, frame, palette):
        super().__init__(parent)
        self.canvas = canvas
        self.frame = frame
        self.palette = palette
        self._controls = {}
        self._counters = {}
        self._wrappers = []
        self._in_relayout = False
        self._last_relayout_width = None

        self.SetBackgroundColour(palette["panel_bg"])
        columns = wx.BoxSizer(wx.HORIZONTAL)
        self.sash = SashHandle(self, frame, palette)
        columns.Add(self.sash, 0, wx.EXPAND)

        outer = wx.BoxSizer(wx.VERTICAL)
        header = wx.BoxSizer(wx.HORIZONTAL)
        self.title = wx.StaticText(self, label="Properties")
        title_font = self.title.GetFont()
        title_font.SetPointSize(title_font.GetPointSize() + 4)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        self.title.SetForegroundColour(palette["text"])
        self.count_label = wx.StaticText(self, label="")
        self.count_label.SetForegroundColour(palette["muted"])
        header.Add(self.title, 0, wx.ALL, 10)
        header.AddStretchSpacer()
        header.Add(self.count_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        outer.Add(header, 0, wx.EXPAND)

        self.subtitle = WrappingLabel(
            self, "Click a shape on the canvas to edit it.", palette["muted"]
        )
        outer.Add(self.subtitle, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.rule = wx.StaticLine(self)
        outer.Add(self.rule, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.scrolled = wx.ScrolledWindow(self)
        self.scrolled.SetBackgroundColour(palette["panel_body_bg"])
        self.scrolled.SetScrollRate(0, 14)
        try:
            self.scrolled.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_DEFAULT)
        except Exception:  # noqa: BLE001 - not available on every backend
            pass
        self.content = wx.BoxSizer(wx.VERTICAL)
        self.scrolled.SetSizer(self.content)
        outer.Add(self.scrolled, 1, wx.EXPAND | wx.ALL, 4)
        columns.Add(outer, 1, wx.EXPAND)
        self.SetSizer(columns)

        self._sync_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_sync_timer, self._sync_timer)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.scrolled.Bind(wx.EVT_SIZE, self._on_size)
        self._sync_timer.Start(300)

        self.RefreshPanel()
        wx.CallAfter(self._relayout)

    def set_palette(self, palette):
        """Apply a new theme palette and rebuild the inspector."""
        self.palette = palette
        self.SetBackgroundColour(palette["panel_bg"])
        self.scrolled.SetBackgroundColour(palette["panel_body_bg"])
        self.title.SetForegroundColour(palette["text"])
        self.count_label.SetForegroundColour(palette["muted"])
        self.subtitle.SetForegroundColour(palette["muted"])
        self.sash.set_palette(palette)
        self.RefreshPanel()

    def _on_size(self, event):
        event.Skip()
        if getattr(self, "_destroyed", False) or self._in_relayout:
            return
        width = self.scrolled.GetClientSize().width
        if width <= 1:
            width = self.GetClientSize().width - 8
        if width <= 1 or width == self._last_relayout_width:
            return
        wx.CallAfter(self._relayout)

    def _relayout(self):
        if getattr(self, "_destroyed", False) or self._in_relayout:
            return
        self._in_relayout = True
        try:
            width = self.scrolled.GetClientSize().width
            if width <= 1:
                width = self.GetClientSize().width - 8
            if width <= 1:
                return
            if self.IsShownOnScreen():
                self._last_relayout_width = width
            content_width = max(120, width - 18)
            for label in list(self._wrappers):
                try:
                    label.wrap_to(content_width)
                except RuntimeError:
                    continue
            try:
                self.subtitle.wrap_to(max(120, self.GetClientSize().width - 20))
            except RuntimeError:
                pass
            self.content.Layout()
            self.scrolled.FitInside()
            self.Layout()
        finally:
            self._in_relayout = False

    def _on_destroy(self, event):
        # Stop the sync timer before teardown: a queued timer event firing
        # on half-destroyed controls segfaults instead of raising.  Child
        # destroys propagate here too, so only react to our own destruction.
        if event.GetEventObject() is not self:
            event.Skip()
            return
        self._destroyed = True
        try:
            self._sync_timer.Stop()
        except RuntimeError:
            pass
        event.Skip()

    # -- public ---------------------------------------------------------------

    def RefreshPanel(self):
        self._sync_timer.Stop()
        try:
            self._rebuild_panel()
        finally:
            if not getattr(self, "_destroyed", False):
                try:
                    self._sync_timer.Start(300)
                except RuntimeError:
                    pass

    def _rebuild_panel(self):
        for child in self.scrolled.GetChildren():
            child.Destroy()
        self.content.Clear()
        self._controls = {}
        self._wrappers = []
        selected = [
            s for s in self.canvas.getSelectedShapes() if not isinstance(s, wxdiagram.core.Node)
        ]
        shapes = [
            s
            for s in (self.canvas.diagram.shapes if self.canvas.diagram else [])
            if getattr(s, "IsShown", lambda: True)()
        ]
        self.count_label.SetLabel(f"{len(shapes)} shape{'s' if len(shapes) != 1 else ''}")
        if len(selected) == 1:
            shape = selected[0]
            self.subtitle.set_text("Click a shape on the canvas to edit it.")
            if isinstance(shape, GroupShape):
                self._build_group(shape)
            elif _is_attached_edge(shape):
                self._build_edge(shape)
            else:
                self._build_single(shape)
        elif len(selected) > 1:
            self.subtitle.set_text("Drag any selected shape to move the group.")
            self._build_multi(selected)
        else:
            self.subtitle.set_text("Click a shape on the canvas to edit it.")
            self._build_empty()
        self._build_tips()
        self._style_fields()
        self._relayout()

    def _style_fields(self):
        """Theme native input controls where the platform allows it."""

        def visit(window):
            for child in window.GetChildren():
                if isinstance(child, (wx.TextCtrl, wx.SpinCtrl, wx.SpinCtrlDouble, wx.Choice)):
                    try:
                        child.SetBackgroundColour(self.palette["field_bg"])
                        child.SetForegroundColour(self.palette["text"])
                    except Exception:  # noqa: BLE001 - native control quirks
                        pass
                elif isinstance(child, (wx.CheckBox, wx.RadioButton)):
                    try:
                        child.SetForegroundColour(self.palette["text"])
                    except Exception:  # noqa: BLE001 - native control quirks
                        pass
                visit(child)

        visit(self.scrolled)

    # -- builders ---------------------------------------------------------------

    def _label(self, text, muted=False, wrap=False):
        colour = self.palette["muted"] if muted else self.palette["text"]
        label = (
            WrappingLabel(self.scrolled, text, colour)
            if wrap
            else wx.StaticText(self.scrolled, label=text)
        )
        if not wrap:
            label.SetForegroundColour(colour)
        if wrap:
            self._wrappers.append(label)
        return label

    def _section(self, label):
        text = wx.StaticText(self.scrolled, label=label)
        font = text.GetFont()
        font.SetPointSize(max(8, font.GetPointSize() - 1))
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        text.SetForegroundColour(self.palette["muted"])
        self.content.Add(text, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)

    def _row(self, label, control, hint=""):
        row = wx.BoxSizer(wx.HORIZONTAL)
        caption = self._label(label)
        caption.SetMinSize(wx.Size(62, -1))
        row.Add(caption, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(control, 1, wx.EXPAND)
        self.content.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        if hint:
            note = self._label(hint, muted=True, wrap=True)
            self.content.Add(note, 0, wx.LEFT | wx.RIGHT | wx.TOP, 2)

    def _button(self, label, handler, danger=False):
        btn = FlatButton(self.scrolled, label, self.palette, handler, danger=danger)
        self.content.Add(btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        return btn

    def _build_empty(self):
        self._section("NO SELECTION")
        card = wx.Panel(self.scrolled)
        card.SetBackgroundColour(self.palette["card_bg"])
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        heading = WrappingLabel(card, "Nothing selected", self.palette["text"], margin=44)
        text = WrappingLabel(
            card,
            "Click a shape, drag a marquee on empty canvas, or add one below.",
            self.palette["muted"],
            margin=44,
        )
        card_sizer.Add(heading, 0, wx.ALL, 10)
        card_sizer.Add(text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        card.SetSizer(card_sizer)
        self.content.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        self._wrappers.extend([heading, text])

        self._section("ADD SHAPE")
        add_sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridSizer(2, 2, 6, 6)
        for kind in ("Rectangle", "Circle", "Ellipse", "Triangle"):
            grid.Add(
                FlatButton(
                    self.scrolled,
                    kind,
                    self.palette,
                    lambda _e, k=kind: self.frame.AddShapeOfKind(k),
                    height=34,
                ),
                1,
                wx.EXPAND,
            )
        add_sizer.Add(grid, 0, wx.EXPAND)
        add_sizer.Add(
            FlatButton(
                self.scrolled,
                "Line",
                self.palette,
                lambda _e: self.frame.AddShapeOfKind("Line"),
                height=34,
            ),
            0,
            wx.EXPAND | wx.TOP,
            6,
        )
        self.content.Add(add_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

    def _build_single(self, shape):
        kind = _kind_name(shape)
        self._section("GENERAL")
        name = wx.TextCtrl(self.scrolled, value=shape.GetName(), style=wx.TE_PROCESS_ENTER)
        name.Bind(wx.EVT_TEXT_ENTER, lambda e, s=shape, c=name: self._commit_name(s, c))
        name.Bind(wx.EVT_KILL_FOCUS, lambda e, s=shape, c=name: (self._commit_name(s, c), e.Skip()))
        self._row("Name", name)
        self._controls["name"] = (shape, name)
        type_row = wx.BoxSizer(wx.HORIZONTAL)
        type_row.Add(self._label(f"Type  {kind}"), 1, wx.ALIGN_CENTER_VERTICAL)
        type_row.Add(self._label(f"#{shape.GetId()}", muted=True), 0, wx.ALIGN_CENTER_VERTICAL)
        self.content.Add(type_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)

        self._section("TRANSFORM")
        if _is_free_line(shape):
            self._build_free_line_endpoints(shape)
        else:
            self._build_position_size(shape, free_aspect_default=False)

        self._section("APPEARANCE")
        if _is_free_line(shape):
            self._build_pen_controls(shape, colour_label="Colour")
        else:
            self._build_fill_controls(shape)
            self._build_pen_controls(shape, colour_label="Border")

        self._section("ARRANGE")
        self._button("Duplicate", lambda e: (self.canvas.duplicate_selected(), self._after_edit()))
        self._button("Bring to Front", lambda e: (self.canvas.bring_to_front(), self._after_edit()))
        self._button("Send to Back", lambda e: (self.canvas.send_to_back(), self._after_edit()))
        self._button(
            "Delete Shape",
            lambda e: (self.canvas.delete_selected(), self._after_edit()),
            danger=True,
        )

    def _build_group(self, group):
        self._section("GENERAL")
        name = wx.TextCtrl(self.scrolled, value=group.GetName(), style=wx.TE_PROCESS_ENTER)
        name.Bind(wx.EVT_TEXT_ENTER, lambda e, s=group, c=name: self._commit_name(s, c))
        name.Bind(wx.EVT_KILL_FOCUS, lambda e, s=group, c=name: (self._commit_name(s, c), e.Skip()))
        self._row("Name", name)
        self._controls["name"] = (group, name)
        kids = len(group.GetChildren())
        self.content.Add(
            self._label(f"Type  Group  ({kids} children)  #{group.GetId()}"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            6,
        )
        self._section("TRANSFORM")
        self._build_position_size(group, free_aspect_default=False)
        self.content.Add(
            self._label("Resizing the frame scales the children with it.", muted=True, wrap=True),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            6,
        )
        self._section("ARRANGE")
        self._button("Ungroup", lambda e: (self.canvas.ungroup_selected(), self._after_edit()))
        self._button("Duplicate", lambda e: (self.canvas.duplicate_selected(), self._after_edit()))
        self._button("Bring to Front", lambda e: (self.canvas.bring_to_front(), self._after_edit()))
        self._button("Send to Back", lambda e: (self.canvas.send_to_back(), self._after_edit()))
        self._button(
            "Delete Group",
            lambda e: (self.canvas.delete_selected(), self._after_edit()),
            danger=True,
        )

    def _build_edge(self, edge):
        self._section("GENERAL")
        name = wx.TextCtrl(self.scrolled, value=edge.GetName(), style=wx.TE_PROCESS_ENTER)
        name.Bind(wx.EVT_TEXT_ENTER, lambda e, s=edge, c=name: self._commit_name(s, c))
        name.Bind(wx.EVT_KILL_FOCUS, lambda e, s=edge, c=name: (self._commit_name(s, c), e.Skip()))
        self._row("Name", name)
        self._controls["name"] = (edge, name)
        frm = getattr(edge, "_from", None)
        to = getattr(edge, "_to", None)
        frm_name = frm.GetName() or _kind_name(frm) if frm is not None else "?"
        to_name = to.GetName() or _kind_name(to) if to is not None else "?"
        self.content.Add(
            self._label(
                f"Type  Edge  #{edge.GetId()}  ({frm_name} → {to_name})",
                wrap=True,
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            6,
        )
        self._section("STYLE")
        modes = ["straight", "auto", "avoid", "curved", "orthogonal"]
        choice = wx.Choice(self.scrolled, choices=modes)
        try:
            choice.SetSelection(modes.index(edge.GetRouteMode()))
        except ValueError:
            choice.SetSelection(1)
        choice.Bind(wx.EVT_CHOICE, lambda e, s=edge, c=choice: self._commit_route(s, c))
        self._row("Routing", choice)
        self._controls["route"] = (edge, choice)
        arrow_label = "Arrowhead: On" if edge.GetArrows() else "Arrowhead: Off"
        self._button(arrow_label, lambda _e, s=edge: self._toggle_arrow(s))
        self._build_pen_controls(edge, colour_label="Colour")
        self._section("ARRANGE")
        self._button(
            "Delete Edge",
            lambda e: (self.canvas.delete_selected(), self._after_edit()),
            danger=True,
        )

    def _build_multi(self, selected):
        self.content.Add(
            self._label(f"{len(selected)} shapes selected"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            10,
        )
        self.content.Add(
            self._label("Drag any selected shape to move the group.", muted=True, wrap=True),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            2,
        )
        self._section("APPLY TO ALL")
        fill_picker = wx.ColourPickerCtrl(self.scrolled)
        fill_picker.Bind(
            wx.EVT_COLOURPICKER_CHANGED, lambda e, ss=list(selected): self._commit_multi_fill(ss)
        )
        self._row("Fill", fill_picker)
        self._controls["multi_fill"] = (selected, fill_picker)
        pen_picker = wx.ColourPickerCtrl(self.scrolled)
        pen_picker.Bind(
            wx.EVT_COLOURPICKER_CHANGED, lambda e, ss=list(selected): self._commit_multi_pen(ss)
        )
        self._row("Border", pen_picker)
        self._controls["multi_pen"] = (selected, pen_picker)
        self._section("ARRANGE")
        self._button("Group", lambda e: (self.canvas.group_selected(), self._after_edit()))
        self._button("Duplicate", lambda e: (self.canvas.duplicate_selected(), self._after_edit()))
        self._button("Bring to Front", lambda e: (self.canvas.bring_to_front(), self._after_edit()))
        self._button("Send to Back", lambda e: (self.canvas.send_to_back(), self._after_edit()))
        self._button(
            "Delete Selected",
            lambda e: (self.canvas.delete_selected(), self._after_edit()),
            danger=True,
        )

    def _build_tips(self):
        rule = wx.StaticLine(self.scrolled)
        self.content.Add(rule, 0, wx.EXPAND | wx.ALL, 10)
        tips = self._label(
            "Quick tips\n"
            "Drag a shape to move it; drag empty canvas to marquee-select.\n"
            "Shift/Ctrl+click adds or removes shapes.\n"
            "Drag a dot on a selected shape onto another shape to connect them.\n"
            "Space+drag or middle-drag pans; Ctrl+wheel zooms.\n"
            "Corner handles resize (Shift frees the ratio, Alt from centre).\n"
            "Arrow keys nudge by 1 px (Shift = 10 px).\n"
            "Ctrl+Z undoes; Ctrl+D duplicates; Ctrl+G groups.",
            muted=True,
            wrap=True,
        )
        self.content.Add(tips, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

    # -- transform/appearance control builders -----------------------------------

    def _spin(self, value, minimum, maximum, increment=1.0):
        spin = wx.SpinCtrlDouble(self.scrolled, min=minimum, max=maximum, inc=increment)
        spin.SetValue(float(value))
        spin.SetDigits(1)
        return spin

    def _build_position_size(self, shape, free_aspect_default):
        if isinstance(shape, CircleShape):
            x0, y0, x1, y1 = _bbox_of(shape)
            pos_x = self._spin(x0, -10000, 10000)
            pos_y = self._spin(y0, -10000, 10000)
            dia = self._spin(x1 - x0, 8, 4000)
            for ctrl, handler in (
                (pos_x, lambda e, s=shape: self._commit_position(s)),
                (pos_y, lambda e, s=shape: self._commit_position(s)),
                (dia, lambda e, s=shape: self._commit_diameter(s)),
            ):
                ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, handler)
                ctrl.Bind(wx.EVT_TEXT_ENTER, handler)
                ctrl.Bind(wx.EVT_KILL_FOCUS, lambda e, h=handler: (h(None), e.Skip()))
            row = wx.BoxSizer(wx.HORIZONTAL)
            row.Add(self._label("X", muted=True), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
            row.Add(pos_x, 1, wx.EXPAND | wx.RIGHT, 8)
            row.Add(self._label("Y", muted=True), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
            row.Add(pos_y, 1, wx.EXPAND)
            self.content.Add(self._label("Position", muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
            self.content.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 2)
            self._row("Diameter", dia)
            self._controls["pos"] = (shape, pos_x, pos_y)
            self._controls["diameter"] = (shape, dia)
            return

        x0, y0, x1, y1 = _bbox_of(shape)
        pos_x = self._spin(x0, -10000, 10000)
        pos_y = self._spin(y0, -10000, 10000)
        size_w = self._spin(x1 - x0, 1, 4000)
        size_h = self._spin(y1 - y0, 1, 4000)
        for ctrl in (pos_x, pos_y):
            ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, lambda e, s=shape: self._commit_position(s))
            ctrl.Bind(wx.EVT_TEXT_ENTER, lambda e, s=shape: self._commit_position(s))
            ctrl.Bind(wx.EVT_KILL_FOCUS, lambda e, s=shape: (self._commit_position(s), e.Skip()))
        for ctrl in (size_w, size_h):
            ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, lambda e, s=shape: self._commit_size(s))
            ctrl.Bind(wx.EVT_TEXT_ENTER, lambda e, s=shape: self._commit_size(s))
            ctrl.Bind(wx.EVT_KILL_FOCUS, lambda e, s=shape: (self._commit_size(s), e.Skip()))
        self.content.Add(self._label("Position", muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(self._label("X", muted=True), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row.Add(pos_x, 1, wx.EXPAND | wx.RIGHT, 8)
        row.Add(self._label("Y", muted=True), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row.Add(pos_y, 1, wx.EXPAND)
        self.content.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 2)
        self.content.Add(self._label("Size", muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(self._label("W", muted=True), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row2.Add(size_w, 1, wx.EXPAND | wx.RIGHT, 8)
        row2.Add(self._label("H", muted=True), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row2.Add(size_h, 1, wx.EXPAND)
        self.content.Add(row2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 2)
        self._controls["pos"] = (shape, pos_x, pos_y)
        self._controls["size"] = (shape, size_w, size_h)

    def _build_free_line_endpoints(self, shape):
        x1 = wx.SpinCtrlDouble(self.scrolled, min=-10000, max=10000, inc=1.0, value=str(shape.x[0]))
        y1 = wx.SpinCtrlDouble(self.scrolled, min=-10000, max=10000, inc=1.0, value=str(shape.y[0]))
        x2 = wx.SpinCtrlDouble(self.scrolled, min=-10000, max=10000, inc=1.0, value=str(shape.x[1]))
        y2 = wx.SpinCtrlDouble(self.scrolled, min=-10000, max=10000, inc=1.0, value=str(shape.y[1]))
        for ctrl in (x1, y1, x2, y2):
            for evt in (wx.EVT_SPINCTRLDOUBLE, wx.EVT_TEXT_ENTER):
                ctrl.Bind(evt, lambda e, s=shape: self._commit_line_endpoints(s))
            ctrl.Bind(
                wx.EVT_KILL_FOCUS, lambda e, s=shape: (self._commit_line_endpoints(s), e.Skip())
            )
        self.content.Add(self._label("Start", muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(x1, 1, wx.EXPAND | wx.RIGHT, 8)
        row.Add(y1, 1, wx.EXPAND)
        self.content.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 2)
        self.content.Add(self._label("End", muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(x2, 1, wx.EXPAND | wx.RIGHT, 8)
        row2.Add(y2, 1, wx.EXPAND)
        self.content.Add(row2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 2)
        self._controls["line_points"] = (shape, x1, y1, x2, y2)

    def _colour_row(self, current, picker_handler, hex_label_key):
        picker = wx.ColourPickerCtrl(self.scrolled, colour=current)
        picker.Bind(wx.EVT_COLOURPICKER_CHANGED, picker_handler)
        hex_label = self._label(self._hex_of(current), muted=True)
        hex_label.SetMinSize(wx.Size(70, -1))
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(picker, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row.Add(hex_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.content.Add(row, 0, wx.LEFT | wx.RIGHT | wx.TOP, 2)
        self._controls[hex_label_key] = hex_label
        return picker

    def _build_fill_controls(self, shape):
        self.content.Add(self._label("Fill", muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        picker = self._colour_row(
            shape.GetFillColour(),
            lambda e, s=shape: self._commit_fill(s),
            "fill_hex",
        )
        self._controls["fill"] = (shape, picker)
        self.content.Add(
            self._label("Click the swatch to pick a colour.", muted=True, wrap=True),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            2,
        )

    def _build_pen_controls(self, shape, colour_label):
        self.content.Add(self._label(colour_label, muted=True), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        picker = self._colour_row(
            shape.GetPenColour(),
            lambda e, s=shape: self._commit_pen(s),
            "pen_hex",
        )
        self._controls["pen"] = (shape, picker)
        width = self._spin(shape.GetPenWidth(), 1, 20)
        width.Bind(wx.EVT_SPINCTRLDOUBLE, lambda e, s=shape: self._commit_pen_width(s))
        width.Bind(wx.EVT_TEXT_ENTER, lambda e, s=shape: self._commit_pen_width(s))
        width.Bind(wx.EVT_KILL_FOCUS, lambda e, s=shape: (self._commit_pen_width(s), e.Skip()))
        self._row("Width", width)
        self._controls["pen_width"] = (shape, width)

    # -- commits (each is one undo step) ----------------------------------------

    def _after_edit(self):
        self.canvas.update_virtual_size()
        self.canvas.Refresh()
        self.RefreshPanel()
        self.frame.UpdateStatus()

    def _commit_name(self, shape, control):
        value = control.GetValue()
        if value == shape.GetName():
            return
        self.canvas.begin_undo()
        try:
            shape.SetName(value)
        finally:
            self.canvas.commit_undo()
        self.frame.UpdateStatus()

    def _commit_position(self, shape):
        _, ctrl_x, ctrl_y = self._controls.get("pos", (None, None, None))
        if ctrl_x is None:
            return
        new_x, new_y = ctrl_x.GetValue(), ctrl_y.GetValue()
        x0, y0, _, _ = _bbox_of(shape)
        dx, dy = new_x - x0, new_y - y0
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return
        self.canvas.begin_undo()
        try:
            shape.move(dx, dy)
            shape.MoveLinks(dc=None)
        finally:
            self.canvas.commit_undo()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def _commit_diameter(self, shape):
        _, ctrl = self._controls.get("diameter", (None, None))
        if ctrl is None:
            return
        new_d = max(8.0, ctrl.GetValue())
        x0, y0, x1, y1 = _bbox_of(shape)
        old_d = x1 - x0
        if abs(new_d - old_d) < 1e-9:
            return
        self.canvas.begin_undo()
        try:
            shape.x = [x0, x0 + new_d]
            shape.y = [y0, y0 + new_d]
            shape.MoveLinks(dc=None)
        finally:
            self.canvas.commit_undo()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def _commit_size(self, shape):
        entry = self._controls.get("size")
        if entry is None:
            return
        _, ctrl_w, ctrl_h = entry
        new_w = max(1.0, ctrl_w.GetValue())
        new_h = max(1.0, ctrl_h.GetValue())
        x0, y0, x1, y1 = _bbox_of(shape)
        if abs(new_w - (x1 - x0)) < 1e-9 and abs(new_h - (y1 - y0)) < 1e-9:
            return
        self.canvas.begin_undo()
        try:
            if isinstance(shape, GroupShape):
                old = (shape.x[0], shape.y[0], shape.x[1], shape.y[1])
                shape.x = [x0, x0 + new_w]
                shape.y = [y0, y0 + new_h]
                shape._scale_children_to(old, (shape.x[0], shape.y[0], shape.x[1], shape.y[1]))
            elif isinstance(shape, DemoTriangle):
                scale_x = new_w / (x1 - x0) if (x1 - x0) else 1.0
                scale_y = new_h / (y1 - y0) if (y1 - y0) else 1.0
                shape.x = [x0 + (v - x0) * scale_x for v in shape.x]
                shape.y = [y0 + (v - y0) * scale_y for v in shape.y]
            else:
                # Keep the top-left fixed; never invert.
                lo_x, hi_x = (
                    (shape.x[0], shape.x[1])
                    if shape.x[0] <= shape.x[1]
                    else (shape.x[1], shape.x[0])
                )
                lo_y, hi_y = (
                    (shape.y[0], shape.y[1])
                    if shape.y[0] <= shape.y[1]
                    else (shape.y[1], shape.y[0])
                )
                shape.x = [lo_x, lo_x + new_w]
                shape.y = [lo_y, lo_y + new_h]
            shape.MoveLinks(dc=None)
        finally:
            self.canvas.commit_undo()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def _commit_line_endpoints(self, shape):
        entry = self._controls.get("line_points")
        if entry is None:
            return
        _, cx1, cy1, cx2, cy2 = entry
        new = (cx1.GetValue(), cy1.GetValue(), cx2.GetValue(), cy2.GetValue())
        old = (shape.x[0], shape.y[0], shape.x[1], shape.y[1])
        if all(abs(a - b) < 1e-9 for a, b in zip(new, old)):
            return
        self.canvas.begin_undo()
        try:
            shape.x = [new[0], new[2]]
            shape.y = [new[1], new[3]]
            shape.MoveLinks(dc=None)
        finally:
            self.canvas.commit_undo()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def _commit_fill(self, shape):
        _, picker = self._controls.get("fill", (None, None))
        if picker is None:
            return
        colour = picker.GetColour()
        self.canvas.begin_undo()
        try:
            shape.SetFillColour(colour)
        finally:
            self.canvas.commit_undo()
        self._controls["fill_hex"].SetLabel(self._hex_of(colour))
        self.canvas.Refresh()

    def _commit_pen(self, shape):
        _, picker = self._controls.get("pen", (None, None))
        if picker is None:
            return
        colour = picker.GetColour()
        self.canvas.begin_undo()
        try:
            shape.SetPenColour(colour)
            if _is_attached_edge(shape):
                shape.SetBrush(wx.Brush(colour))
        finally:
            self.canvas.commit_undo()
        self._controls["pen_hex"].SetLabel(self._hex_of(colour))
        self.canvas.Refresh()

    def _commit_pen_width(self, shape):
        entry = self._controls.get("pen_width")
        if entry is None:
            return
        _, ctrl = entry
        width = max(1, int(ctrl.GetValue()))
        if width == shape.GetPenWidth():
            return
        self.canvas.begin_undo()
        try:
            shape.SetPenWidth(width)
        finally:
            self.canvas.commit_undo()
        self.canvas.Refresh()

    def _commit_route(self, edge, choice):
        self.canvas.begin_undo()
        try:
            edge.SetRouteMode(choice.GetStringSelection())
        finally:
            self.canvas.commit_undo()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()

    def _toggle_arrow(self, edge):
        self.canvas.begin_undo()
        try:
            if edge.GetArrows():
                for arrow in list(edge.GetArrows()):
                    if arrow.GetArrowEnd() == wxdiagram.ARROW_POSITION_END:
                        edge._arcArrows.remove(arrow)
            else:
                edge.AddArrow(wxdiagram.ARROW_ARROW, wxdiagram.ARROW_POSITION_END, size=12.0)
        finally:
            self.canvas.commit_undo()
        self.RefreshPanel()
        self.canvas.Refresh()

    def _commit_multi_fill(self, shapes):
        _, picker = self._controls.get("multi_fill", (None, None))
        if picker is None:
            return
        colour = picker.GetColour()
        self.canvas.begin_undo()
        try:
            for shape in shapes:
                if not _is_free_line(shape) and not _is_attached_edge(shape):
                    shape.SetFillColour(colour)
                else:
                    shape.SetPenColour(colour)
        finally:
            self.canvas.commit_undo()
        self.canvas.Refresh()

    def _commit_multi_pen(self, shapes):
        _, picker = self._controls.get("multi_pen", (None, None))
        if picker is None:
            return
        colour = picker.GetColour()
        self.canvas.begin_undo()
        try:
            for shape in shapes:
                shape.SetPenColour(colour)
                if _is_attached_edge(shape):
                    shape.SetBrush(wx.Brush(colour))
        finally:
            self.canvas.commit_undo()
        self.canvas.Refresh()

    # -- live sync while dragging --------------------------------------------------

    def _on_sync_timer(self, event):
        selected = [
            s for s in self.canvas.getSelectedShapes() if not isinstance(s, wxdiagram.core.Node)
        ]
        if len(selected) != 1:
            return
        shape = selected[0]
        focused = wx.Window.FindFocus()
        try:
            if "pos" in self._controls:
                _, cx, cy = self._controls["pos"]
                x0, y0, _, _ = _bbox_of(shape)
                if cx is not focused and cy is not focused:
                    if abs(cx.GetValue() - x0) > 0.05:
                        cx.SetValue(x0)
                    if abs(cy.GetValue() - y0) > 0.05:
                        cy.SetValue(y0)
            if "size" in self._controls:
                _, cw, ch = self._controls["size"]
                _, _, x1, y1 = _bbox_of(shape)
                x0, y0, _, _ = _bbox_of(shape)
                if cw is not focused and abs(cw.GetValue() - (x1 - x0)) > 0.05:
                    cw.SetValue(x1 - x0)
                if ch is not focused and abs(ch.GetValue() - (y1 - y0)) > 0.05:
                    ch.SetValue(y1 - y0)
        except RuntimeError:
            # Controls were rebuilt mid-sync; the next tick picks them up.
            pass

    @staticmethod
    def _hex_of(colour):
        return "#%02X%02X%02X" % (colour.Red(), colour.Green(), colour.Blue())


# -- main frame ---------------------------------------------------------------------


class ShapesDemoFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Shape Studio (wxdiagram)", size=(1200, 760))
        self.Centre()
        self._counters = {}
        self.theme_name = "system"
        self.palette = resolve_theme(self.theme_name)

        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(260)

        self.canvas = wxdiagram.ShapeCanvas(self.splitter)
        self.canvas.SetBackgroundColour(self.palette["canvas_bg"])
        self.canvas.SetDiagram(wxdiagram.Diagram())
        self.canvas.showDropPorts = False
        self.canvas.Bind(wx.EVT_RIGHT_UP, self.OnCanvasRightClick)

        self.panel = PropertiesPanel(self.splitter, self.canvas, self, self.palette)
        self.splitter.SplitVertically(self.canvas, self.panel, -PANEL_WIDTH)
        self.canvas.onSelectionChanged = lambda c: (self.panel.RefreshPanel(), self.UpdateStatus())

        self._create_menus()
        self.CreateStatusBar(2)
        self.SetStatusWidths([-1, 420])
        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self._on_system_colour_changed)
        self._apply_theme()
        self.UpdateStatus()
        self._seed_scene()

    def _apply_theme(self):
        palette = resolve_theme(self.theme_name)
        self._retint_edges(self.palette.get("edge"), palette["edge"])
        self.palette = palette
        self.SetBackgroundColour(palette["window_bg"])
        self.splitter.SetBackgroundColour(palette["window_bg"])
        self.canvas.SetBackgroundColour(palette["canvas_bg"])
        self.canvas.gridColour = palette["grid"]
        self.canvas.guideColour = palette["guide"]
        self.canvas.handleFillColour = palette["handle_fill"]
        self.canvas.handleOutlineColour = palette["handle_outline"]
        self.canvas.portFillColour = palette["port_fill"]
        self.canvas.portOutlineColour = palette["port_outline"]
        self.canvas.marqueePenColour = palette["marquee"]
        self.canvas.connectionPenColour = palette["connection"]
        self.canvas.edgePenColour = palette["edge"]
        status = self.GetStatusBar()
        if status is not None:
            status.SetBackgroundColour(palette["window_bg"])
            status.SetForegroundColour(palette["text"])
        self.panel.set_palette(palette)
        for key, item in getattr(self, "_theme_items", {}).items():
            item.Check(key == self.theme_name)
        self.canvas.Refresh()
        self.Refresh()

    def _retint_edges(self, old_colour, new_colour):
        """Re-colour default edges so they stay visible across theme changes."""
        if old_colour is None or new_colour is None or self.canvas.diagram is None:
            return
        old_key = (old_colour.Red(), old_colour.Green(), old_colour.Blue())
        black = (0, 0, 0)
        for shape in self.canvas.diagram.shapes:
            if not _is_attached_edge(shape):
                continue
            colour = shape.GetPenColour()
            key = (colour.Red(), colour.Green(), colour.Blue())
            if key == old_key or key == black:
                shape.SetPenColour(new_colour)
                shape.SetBrush(wx.Brush(new_colour))
                if shape.GetPenWidth() < 2:
                    shape.SetPenWidth(2)

    def OnTheme(self, event):
        for key, item in getattr(self, "_theme_items", {}).items():
            if item.GetId() == event.GetId():
                self.theme_name = key
                self._apply_theme()
                return

    def _on_system_colour_changed(self, event):
        if self.theme_name == "system":
            self._apply_theme()
        event.Skip()

    # -- status ------------------------------------------------------------------

    def UpdateStatus(self):
        shapes = self.canvas.diagram.shapes if self.canvas.diagram else []
        selected = [
            s for s in self.canvas.getSelectedShapes() if not isinstance(s, wxdiagram.core.Node)
        ]
        if selected:
            names = ", ".join((s.GetName() or _kind_name(s)) for s in selected[:3])
            if len(selected) > 3:
                names += f" +{len(selected) - 3} more"
            sel_text = f"Selected: {names}"
        else:
            sel_text = "Selected: None"
        self.SetStatusText(f"Shapes: {len(shapes)}   |   {sel_text}", 0)
        self.SetStatusText(
            "Space/middle-drag pan · Ctrl+wheel zoom · Shift free-resize · Alt from centre", 1
        )

    # -- shape creation ----------------------------------------------------------

    def _viewport_centre(self):
        client_w, client_h = self.canvas.GetClientSize()
        return self.canvas.client_pos_in_diagram_coords(client_w / 2, client_h / 2)

    def _next_name(self, kind):
        self._counters[kind] = self._counters.get(kind, 0) + 1
        return f"{kind} {self._counters[kind]}"

    def AddShapeOfKind(self, kind, centre=None):
        cx, cy = centre or self._viewport_centre()
        w, h = DEFAULT_SIZES[kind]
        if kind == "Rectangle":
            shape = DemoRect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        elif kind == "Circle":
            shape = CircleShape(cx - w / 2, cy - w / 2, w)
        elif kind == "Ellipse":
            shape = wxdiagram.ConnectableEllipseShape()
            shape.x = [cx - w / 2, cx + w / 2]
            shape.y = [cy - h / 2, cy + h / 2]
        elif kind == "Triangle":
            shape = DemoTriangle(
                [(cx, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
            )
        elif kind == "Line":
            shape = DemoLine([(cx - w / 2, cy - h / 4), (cx + w / 2, cy + h / 4)])
            shape.SetPenWidth(4)
        else:  # pragma: no cover - guarded by the Add menu
            return None
        if not _is_free_line(shape):
            shape.SetFillColour(PALETTE[kind])
            shape.SetPenColour(wx.Colour(40, 40, 40))
        else:
            shape.SetPenColour(PALETTE[kind])
        shape.SetName(self._next_name(kind))
        self.canvas.InsertShape(shape, 999)
        self.canvas.deselect()
        self.canvas.select(shape)
        self.canvas.update_virtual_size()
        self.canvas.Refresh()
        self.panel.RefreshPanel()
        self.UpdateStatus()
        return shape

    def _seed_scene(self):
        # A small starter scene so first launch is not an empty canvas.
        cx, cy = 400, 300
        self.AddShapeOfKind("Rectangle", centre=(cx - 180, cy - 120))
        self.AddShapeOfKind("Circle", centre=(cx + 140, cy - 120))
        self.AddShapeOfKind("Triangle", centre=(cx - 180, cy + 130))
        self.AddShapeOfKind("Ellipse", centre=(cx + 140, cy + 130))
        self.AddShapeOfKind("Line", centre=(cx + 140, cy + 300))
        self.canvas.deselect()
        self.canvas.update_virtual_size()
        self.canvas.ZoomToFit()

    # -- menus -------------------------------------------------------------------

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
        return item

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
        self._add_item(
            edit_menu, "&Undo\tCtrl+Z", lambda e: self._after_canvas_op(self.canvas.undo)
        )
        self._add_item(
            edit_menu, "&Redo\tCtrl+Shift+Z", lambda e: self._after_canvas_op(self.canvas.redo)
        )
        self._add_item(
            edit_menu,
            "&Duplicate\tCtrl+D",
            lambda e: self._after_canvas_op(self.canvas.duplicate_selected),
        )
        self._add_item(
            edit_menu, "&Delete\tDel", lambda e: self._after_canvas_op(self.canvas.delete_selected)
        )
        edit_menu.AppendSeparator()
        self._add_item(
            edit_menu, "&Group\tCtrl+G", lambda e: self._after_canvas_op(self.canvas.group_selected)
        )
        self._add_item(
            edit_menu,
            "&Ungroup\tCtrl+Shift+G",
            lambda e: self._after_canvas_op(self.canvas.ungroup_selected),
        )
        edit_menu.AppendSeparator()
        self._add_item(edit_menu, "Select &All\tCtrl+A", self.OnSelectAll)
        self._add_item(
            edit_menu, "&Deselect\tEsc", lambda e: self._after_canvas_op(self.canvas.deselect)
        )

        add_menu = self._menu("&Add")
        for kind, shortcut in (
            ("Rectangle", "Ctrl+1"),
            ("Circle", "Ctrl+2"),
            ("Ellipse", "Ctrl+3"),
            ("Triangle", "Ctrl+4"),
            ("Line", "Ctrl+5"),
        ):
            self._add_item(
                add_menu,
                f"&{kind}\t{shortcut}",
                lambda e, k=kind: self.AddShapeOfKind(k),
                f"Add a {kind.lower()}",
            )
        add_menu.AppendSeparator()
        self._add_item(
            add_menu,
            "&Connect selected\tCtrl+J",
            self.OnConnect,
            "Draw an attached edge between the two selected shapes",
        )

        arrange_menu = self._menu("&Arrange")
        self._add_item(
            arrange_menu,
            "Bring to &Front",
            lambda e: self._after_canvas_op(self.canvas.bring_to_front),
        )
        self._add_item(
            arrange_menu,
            "Bring F&orward",
            lambda e: self._after_canvas_op(self.canvas.bring_forward),
        )
        self._add_item(
            arrange_menu,
            "Send Back&ward",
            lambda e: self._after_canvas_op(self.canvas.send_backward),
        )
        self._add_item(
            arrange_menu, "Send to &Back", lambda e: self._after_canvas_op(self.canvas.send_to_back)
        )

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
        theme_menu = wx.Menu()
        self._theme_items = {}
        for label, key in (("&System", "system"), ("&Light", "light"), ("&Dark", "dark")):
            item = theme_menu.AppendRadioItem(wx.ID_ANY, label)
            item.Check(self.theme_name == key)
            self.Bind(wx.EVT_MENU, self.OnTheme, item)
            self._theme_items[key] = item
        view_menu.AppendSubMenu(theme_menu, "&Theme")
        view_menu.AppendSeparator()
        self._add_item(view_menu, "Zoom &In\tCtrl+=", lambda e: self.canvas.ZoomIn(anchor="center"))
        self._add_item(
            view_menu, "Zoom &Out\tCtrl+-", lambda e: self.canvas.ZoomOut(anchor="center")
        )
        self._add_item(view_menu, "Zoom to &Fit\tCtrl+F", lambda e: self.canvas.ZoomToFit())
        self._add_item(view_menu, "R&eset Zoom\tCtrl+0", lambda e: self.canvas.ZoomReset())

        help_menu = self._menu("&Help")
        self._add_item(help_menu, "&About", self.OnAbout, "About this demo")
        self._add_item(help_menu, "&Shortcuts", self.OnShortcuts, "Keyboard shortcuts")

    def _after_canvas_op(self, func, *args):
        func(*args)
        self.panel.RefreshPanel()
        self.UpdateStatus()

    # -- context menus -------------------------------------------------------------

    def OnCanvasRightClick(self, event):
        shape = self.canvas.getCurrentShape(event)
        if hasattr(shape, "item"):  # right-clicked on a resize handle
            shape = shape.item
        if shape is not None:
            if shape not in self.canvas.getSelectedShapes():
                self.canvas.deselect()
                self.canvas.select(shape)
                self.panel.RefreshPanel()
                self.UpdateStatus()
            menu = self._shape_menu(shape)
        else:
            menu = self._canvas_menu()
        try:
            self.canvas.PopupMenu(menu, event.GetPosition())
        finally:
            menu.Destroy()

    def _show_popup(self, menu, position):
        try:
            self.canvas.PopupMenu(menu, position)
        finally:
            menu.Destroy()

    def _popup_item(self, menu, label, handler):
        item = menu.Append(wx.ID_ANY, label)
        self.Bind(wx.EVT_MENU, handler, item)

    def _canvas_menu(self):
        menu = wx.Menu()
        add = wx.Menu()
        for kind in ("Rectangle", "Circle", "Ellipse", "Triangle", "Line"):
            item = add.Append(wx.ID_ANY, kind)
            self.Bind(wx.EVT_MENU, lambda e, k=kind: self.AddShapeOfKind(k), item)
        menu.AppendSubMenu(add, "Add")
        menu.AppendSeparator()
        self._popup_item(menu, "Select All", lambda e: self.OnSelectAll(e))
        self._popup_item(menu, "Deselect", lambda e: self._after_canvas_op(self.canvas.deselect))
        menu.AppendSeparator()
        self._popup_item(menu, "Zoom In", lambda e: self.canvas.ZoomIn(anchor="center"))
        self._popup_item(menu, "Zoom Out", lambda e: self.canvas.ZoomOut(anchor="center"))
        self._popup_item(menu, "Zoom to Fit", lambda e: self.canvas.ZoomToFit())
        self._popup_item(menu, "Reset Zoom", lambda e: self.canvas.ZoomReset())
        return menu

    def _shape_menu(self, shape):
        menu = wx.Menu()
        self._popup_item(
            menu, "Bring to Front", lambda e: self._after_canvas_op(self.canvas.bring_to_front)
        )
        self._popup_item(
            menu, "Bring Forward", lambda e: self._after_canvas_op(self.canvas.bring_forward)
        )
        self._popup_item(
            menu, "Send Backward", lambda e: self._after_canvas_op(self.canvas.send_backward)
        )
        self._popup_item(
            menu, "Send to Back", lambda e: self._after_canvas_op(self.canvas.send_to_back)
        )
        menu.AppendSeparator()
        self._popup_item(
            menu, "Duplicate", lambda e: self._after_canvas_op(self.canvas.duplicate_selected)
        )
        self._popup_item(
            menu, "Delete", lambda e: self._after_canvas_op(self.canvas.delete_selected)
        )
        selected = [
            s for s in self.canvas.getSelectedShapes() if not isinstance(s, wxdiagram.core.Node)
        ]
        if len(selected) > 1:
            self._popup_item(
                menu, "Group", lambda e: self._after_canvas_op(self.canvas.group_selected)
            )
        if any(isinstance(s, GroupShape) for s in selected):
            self._popup_item(
                menu, "Ungroup", lambda e: self._after_canvas_op(self.canvas.ungroup_selected)
            )
        if _is_attached_edge(shape):
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
                    lambda e, s=shape, m=mode: (s.SetRouteMode(m), self.canvas.Refresh()),
                    item,
                )
        return menu

    # -- menu handlers ---------------------------------------------------------------

    def OnToggleRaiseClicked(self, event):
        self.canvas.bringClickedShapeToFront = self.item_raise.IsChecked()

    def OnToggleGrid(self, event):
        self.canvas.showGrid = self.item_grid.IsChecked()
        self.canvas.Refresh()

    def OnToggleSnap(self, event):
        self.canvas.snapToGrid = self.item_snap.IsChecked()

    def OnToggleGuides(self, event):
        self.canvas.alignmentGuides = self.item_guides.IsChecked()

    def OnSelectAll(self, event):
        self.canvas.deselect()
        for shape in self.canvas.GetDiagram().shapes:
            if getattr(shape, "marqueeSelectable", True):
                self.canvas.select(shape)
        self.panel.RefreshPanel()
        self.UpdateStatus()

    def OnConnect(self, event):
        connectable = [
            s
            for s in self.canvas.getSelectedShapes()
            if not isinstance(s, wxdiagram.core.Node) and not _is_attached_edge(s)
        ]
        if len(connectable) == 2:
            line = self.canvas.join_shapes(connectable[0], connectable[1])
            if line is not None:
                self.canvas.select(line)
            self.canvas.update_virtual_size()
            self.canvas.Refresh()
            self.panel.RefreshPanel()
            self.UpdateStatus()
        else:
            wx.MessageBox(
                "Select two shapes first, then Add > Connect selected",
                "Shape Studio",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )

    def OnNew(self, event):
        self.canvas.SetDiagram(wxdiagram.Diagram())
        self.canvas.clear_undo()
        self.canvas.deselect()
        self.canvas.update_virtual_size()
        self.canvas.Refresh()
        self.panel.RefreshPanel()
        self.UpdateStatus()

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
                wx.MessageBox(f"Could not load:\n{e}", "Shape Studio", wx.OK | wx.ICON_ERROR, self)
                return
            self.canvas.SetDiagram(diagram)
            self.canvas.clear_undo()
            self.canvas.deselect()
            self._apply_theme()
            self.canvas.update_virtual_size()
            self.canvas.ZoomToFit()
            self.panel.RefreshPanel()
            self.UpdateStatus()

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
            self.SetStatusText(f"Saved {path}", 0)

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
                self.SetStatusText(f"Exported {path}", 0)
            else:
                wx.MessageBox(
                    f"Could not write {path}", "Shape Studio", wx.OK | wx.ICON_ERROR, self
                )

    def OnAbout(self, event):
        wx.MessageBox(
            "Shape Studio (wxdiagram)\n\n"
            "A Shape Studio-style editor proving that wxdiagram supports "
            "shape apps: add/resize/group shapes, edit colours and geometry "
            "in the properties panel, and connect shapes with attached edges.",
            "About Shape Studio",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    def OnShortcuts(self, event):
        wx.MessageBox(
            "Drag shape: move · Drag empty canvas: marquee-select\n"
            "Shift/Ctrl+click: add/remove selection · Esc: deselect\n"
            "Space/middle-drag: pan · Ctrl+wheel: zoom\n"
            "Shift resize: free aspect · Alt resize: from centre\n"
            "Arrows: nudge (Shift = 10 px)\n"
            "Ctrl+Z / Ctrl+Shift+Z: undo/redo · Ctrl+D: duplicate\n"
            "Ctrl+G / Ctrl+Shift+G: group/ungroup · Del: delete",
            "Keyboard shortcuts",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    def OnExit(self, event):
        self.Close()


def main():
    app = wx.App(redirect=False)
    frame = ShapesDemoFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
