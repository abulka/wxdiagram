##########################################
# OGLlike - OGL like library for wxPython
#
# Copyright (C) Andy Bulka 2019 for my additions
#   Phoenix compatibility and various improvements.
#   Plus many changes to try and add more ogl features to suit pynsource's usage
#   License: MIT (see LICENSE.md)
#
# Copyright (C) 2003-2004  Erik R. Lechak
# Feel free to use it, modify it, distribute it.  All I ask is:
#   1)  If you improve it, please send me a copy of the improved version.
#   2)  Please don't try to take credit for my work.
##########################################

import wx
from wx import (
    EVT_KEY_DOWN,
    EVT_KEY_UP,
    EVT_LEFT_DCLICK,
    EVT_LEFT_DOWN,
    EVT_LEFT_UP,
    EVT_MOTION,
    EVT_PAINT,
    EVT_RIGHT_DCLICK,
    EVT_RIGHT_DOWN,
    EVT_RIGHT_UP,
    GetMousePosition,
    PaintDC,
    Pen,
    Brush,
    ScrolledWindow,
    SOLID,
)
from typing import List

import copy
import itertools
from .geometry import (
    ATTACHMENT_MODE_NONE,
    ContinueDraggingLeft,
    FORMAT_CENTRE_HORIZ,
    FORMAT_CENTRE_VERT,
    FORMAT_SIZE_TO_CONTENTS,
    NoDragging,
    CentreText,
    DrawFormattedText,
    FindEndForBox,
    FormatText,
    GetCentredTextExtent,
)
from .basic import ShapeTextLine, ShapeRegion, get_white_background_brush, get_white_background_pen

# Global Stuff   -------------------------------------------------------------------------
clipboard = []

# ANDY
# ANDYMAIN = None
DEBUG_DRAG = False
DEBUG_CONNECT = False
DEBUG_INODE_CONNECT = False
##############


# ------------------------------------------------------------------------------------------


_shape_id_counter = itertools.count(1)


class Diagram:
    def __init__(self):
        self.shapes = []
        self._diagramCanvas = None
        # Grid: spacing in diagram units.  Snapping is off by default so
        # existing diagrams drag exactly as before.
        self._gridSpacing = 10
        self._snapToGrid = False

    # --- Grid / snapping (classic OGL API) --------------------------------

    def SetGridSpacing(self, spacing):
        """Set the grid spacing in diagram units (0 or less disables it)."""
        self._gridSpacing = max(0, int(spacing))

    def GetGridSpacing(self):
        """Return the grid spacing in diagram units."""
        return self._gridSpacing

    def SetSnapToGrid(self, snap):
        """Turn snapping to the grid on or off."""
        self._snapToGrid = bool(snap)

    def GetSnapToGrid(self):
        """Return whether dragging snaps to the grid."""
        return self._snapToGrid

    def Snap(self, x, y):
        """Return ``(x, y)`` rounded to the nearest grid point."""
        spacing = self._gridSpacing
        if spacing <= 0:
            return x, y
        return round(x / spacing) * spacing, round(y / spacing) * spacing

    @staticmethod
    def _ensure_shape_id(shape):
        if getattr(shape, "GetId", None) is not None and shape.GetId() == 0:
            shape.AssignNewIds()
        for child in getattr(shape, "_compositeChildren", []) or []:
            Diagram._ensure_shape_id(child)

    def Save(self, path):
        """Save the diagram to a JSON file (see :mod:`wxdiagram.persistence`)."""
        from . import persistence

        persistence.save(self, path)

    @classmethod
    def Load(cls, path):
        """Load a diagram from a JSON file (see :mod:`wxdiagram.persistence`)."""
        from . import persistence

        return persistence.load(path)

    def _attach_canvas(self, shape):
        canvas = self.GetCanvas()
        if canvas is not None:
            shape.SetCanvas(canvas)

    def AddShape(self, shape, addAfter=None):
        self._ensure_shape_id(shape)
        if addAfter:
            self.shapes.insert(self.shapes.index(addAfter) + 1, shape)
        else:
            self.shapes.insert(0, shape)
        self._attach_canvas(shape)

    def AppendShape(self, shape):
        self._ensure_shape_id(shape)
        self.shapes.append(shape)
        self._attach_canvas(shape)

    def InsertShape(self, shape, index=0):
        self._ensure_shape_id(shape)
        self.shapes.insert(index, shape)
        self._attach_canvas(shape)

    def SetCanvas(self, canvas):
        """Set the shape canvas associated with this diagram."""
        self._diagramCanvas = canvas

    def GetCanvas(self):
        """Return the shape canvas associated with this diagram."""
        return self._diagramCanvas

    def ShowAll(self, show):
        """Call Show for each shape in the diagram."""
        for shape in self.shapes:
            shape.Show(show)

    def Clear(self, dc):
        """Clear the device context, as classic OGL does.

        Use :meth:`DeleteAllShapes` to remove the diagram's shapes.
        """
        if dc is not None:
            dc.Clear()

    def FindShape(self, shape_id):
        """Return the shape with the given id, or None.

        Searches top-level shapes and composite children.
        """

        def find(shape):
            if getattr(shape, "GetId", None) is not None and shape.GetId() == shape_id:
                return shape
            for child in getattr(shape, "_compositeChildren", []) or []:
                found = find(child)
                if found is not None:
                    return found
            return None

        for shape in self.shapes:
            found = find(shape)
            if found is not None:
                return found
        return None

    def DeleteShape(self, shape):
        self.shapes.remove(shape)

    def PopShape(self, index=-1):
        return self.shapes.pop(index)

    def DeleteAllShapes(self):
        del self.shapes[:]

    def ChangeShapeOrder(self, shape, pos=0):
        self.shapes.remove(shape)
        self.shapes.insert(pos, shape)

    def GetCount(self):
        return len(self.shapes)

    def GetShapeList(self):
        return self.shapes


# Generic Shape Event Handler -------------------------------------------------------------------------------
class ShapeEvtHandler:
    def OnLeftUp(self, event):
        pass

    def OnLeftDown(self, event):
        pass

    def OnLeftDClick(self, event):
        pass

    def OnRightUp(self, event):
        pass

    def OnRightDown(self, event):
        pass

    def OnRightDClick(self, event):
        pass

    def OnSelect(self, event):
        pass

    def OnDeselect(self, event):
        pass

    def OnMove(self, event):
        pass

    def OnResize(self, event):
        pass

    def OnConnect(self, event):
        pass

    # ANDY ADDED

    def OnEndDragLeft(self, event):
        pass

    def SetShape(self, sh):
        """
        Set associated shape

        :param `sh`:  the shape, an instance of :class:`Shape`

        """
        # self._handlerShape = sh

    def GetShape(self):
        """Get associated shape."""
        # return self._handlerShape
        return self  # ANDY HACK?

    def SetPreviousHandler(self, handler):
        """
        Set previous event handler.

        :param `handler`: the previous handler, an instance of
         :class:`ShapeEvtHandler` ???

        """
        # self._previousHandler = handler

    def GetPreviousHandler(self):
        """Get previous event handler."""
        # return self._previousHandler
        return None  # ANDY HACK

    def GetEventHandler(self):
        """Get the event handler for this shape."""
        # return self._eventHandler
        return self  # ANDY HACK

    def SetEventHandler(self, handler):
        """Set the event handler for this shape.

        :param `handler`: an instance of :class:`ShapeEvtHandler`

        """
        # self._eventHandler = handler


# Generic Graphic items ---------------------------------------------------------------------------------------
class Shape(ShapeEvtHandler):
    GraphicsInSizeToContents = False  # ANDY ADDED - needed by divided text formatting as a flag
    #: include this shape in marquee selection
    marqueeSelectable = True

    def __init__(self, x=[], y=[]):
        self.x = x  # list of x coord
        self.y = y  # list of y coords
        self.pen = ["BLACK", 1]  # pen color and size
        self.fill = ["WHITE"]  # fill color

        # ANDY EXTRAS
        self._lines = []
        self._controlPoints = []
        self._attachmentPoints = []

        self._regions = []
        self._centreResize = False
        self._canvas = None  # canvas - should come from init
        self._id = 0
        self._visible = True
        self._textMarginX = 5
        self._textMarginY = 5
        # these real objects override the default ogl behaviour of creating a pen/brush each time in the root draw method
        self._pen = None
        self._brush = None

    def draw(self, dc):
        # ANDY ENHANCED to respect _pen, _brush
        # print(f"ROOT DRAW pen "
        #       f"pen: {self.pen} _pen {self._pen} {self._pen.Colour if self._pen else ''}"
        #       f"fill/brush {self.fill} _brush {self._brush} {self._brush.Colour if self._brush else ''}"
        #       f"")
        if self._pen:
            dc.SetPen(self._pen)
        else:
            dc.SetPen(Pen(self.pen[0], self.pen[1], SOLID))

        if self._brush:
            dc.SetBrush(self._brush)
        else:
            dc.SetBrush(Brush(self.fill[0], SOLID))

    def SetPen(self, pen):
        # Pens are the line colour, width and style (e.g. solid, dashed).
        # ogllike only supports pens as strings, and instantiates them
        # in its draw() method.  And it doesn't support pen styles, only SOLID.
        # Easy enough to enhance though...
        # NEW: Passing a pen object (not just a string) will override the ogllike stuff.
        self._pen = pen

    def SetBrush(self, brush):
        # Brushes are the fill e.g. solid, transparent, crosshatched etc.
        # ogllike only support brushes as a string
        # NEW: Passing a brush object (not just a string) will override the ogllike stuff.
        self._brush = brush

    def move(self, x, y):  # should be renamed move_by() cos its a relative move from current pos
        self.x = list(map((lambda v: v + x), self.x))
        self.y = list(map((lambda v: v + y), self.y))

    def Copy(self):
        """Return a detached copy of this shape.

        wx objects (fonts, pens, brushes, bitmaps) are shared, not deep-copied:
        they are native handles and cannot be pickled.  Geometry and region text
        are copied, while attached lines and the graph-node back-reference are
        cleared so a duplicate starts clean.
        """
        clone = copy.copy(self)
        clone.x = list(self.x)
        clone.y = list(self.y)
        clone.pen = list(self.pen)
        clone.fill = list(self.fill)
        clone._id = 0
        clone._regions = [ShapeRegion(region) for region in self._regions]
        clone._controlPoints = []
        clone._lines = []
        clone._attachmentPoints = list(self._attachmentPoints)

        for key, value in vars(self).items():
            if key in {
                "x",
                "y",
                "pen",
                "fill",
                "_regions",
                "_controlPoints",
                "_lines",
                "_attachmentPoints",
                "_canvas",
                "_parent",
                "_compositeChildren",
                "_children",
                "node",
                "_lineControlPoints",
                "_arcArrows",
            }:
                continue
            if isinstance(value, (list, dict, set)):
                clone.__dict__[key] = copy.copy(value)

        # Line geometry lives in RealPoint objects, not x/y.
        if getattr(self, "_lineControlPoints", None):
            clone._lineControlPoints = [wx.RealPoint(p[0], p[1]) for p in self._lineControlPoints]
        if getattr(self, "_arcArrows", None):
            clone._arcArrows = list(self._arcArrows)

        for attr in ("_compositeChildren", "_children"):
            children = getattr(self, attr, None)
            if children:
                copied = [child.Copy() for child in children]
                for child in copied:
                    if hasattr(child, "_parent"):
                        child._parent = clone
                clone.__dict__[attr] = copied

        if hasattr(clone, "node"):
            clone.node = None

        clone.AssignNewIds()
        return clone

    def SetId(self, shape_id):
        """Set the integer identifier for this shape."""
        self._id = shape_id

    def GetId(self):
        """Return the integer identifier for this shape."""
        return getattr(self, "_id", 0)

    def AssignNewIds(self):
        """Assign a new id to this shape and any composite children."""
        self._id = next(_shape_id_counter)
        for child in getattr(self, "_compositeChildren", []) or []:
            child.AssignNewIds()

    # ANDY EXTRAS

    # _xpos and _ypos are centre based, as are GetX() and GetY()

    @property
    def _xpos(self):
        width, height = self.GetBoundingBoxMin()

        # hack for Lines (_lineControlPoints based boundbox) and Shapes (which have 0,0 boundbox)
        # at one stage I had the additional  and len(self._lineControlPoints) == 0)
        if width == 0 or hasattr(self, "_lineControlPoints"):
            width = self.x[1] - self.x[0]
        return self.x[0] + width / 2  # centre x

    @_xpos.setter
    def _xpos(self, value):
        x = value - self._xpos  # difference in centers
        self.x = list(map((lambda v: v + x), self.x))

    @property
    def _ypos(self):
        width, height = self.GetBoundingBoxMin()
        if height == 0 or hasattr(self, "_lineControlPoints"):
            height = self.y[1] - self.y[0]
        return self.y[0] + height / 2  # centre y

    @_ypos.setter
    def _ypos(self, value):
        y = value - self._ypos  # difference in centers
        self.y = list(map((lambda v: v + y), self.y))

    def GetX(self):
        """Get the x position of the centre of the shape."""
        return self._xpos

    def GetY(self):
        """Get the y position of the centre of the shape."""
        return self._ypos

    def SetX(self, x):
        """
        Set the x position of the shape.

        :param `x`: the x position
        """
        self._xpos = x

    def SetY(self, y):
        """
        Set the y position of the shape.

        :param `y`: the y position

        """
        self._ypos = y

    # _width, _height only exist for Rectangles, so moved getters/setters there...

    def GetBoundingBoxMax(self):
        """
        Get the maximum bounding box for the shape, taking into account
        external features such as shadows.
        """
        ww, hh = self.GetBoundingBoxMin()
        # if self._shadowMode != SHADOW_NONE:
        #     ww += self._shadowOffsetX
        #     hh += self._shadowOffsetY
        return ww, hh

    def GetBoundingBoxMin(self):
        """
        Get the minimum bounding box for the shape, that defines the area
        available for drawing the contents (such as text).

        Must be overridden.
        """
        return 0, 0

    def GetBackgroundPen(self):
        """Return pen of the right colour for the background."""
        if self.GetCanvas():
            return wx.Pen(self.GetCanvas().GetBackgroundColour(), 1, wx.PENSTYLE_SOLID)
        return get_white_background_pen()

    def GetBackgroundBrush(self):
        """Return brush of the right colour for the background."""
        if self.GetCanvas():
            return wx.Brush(self.GetCanvas().GetBackgroundColour(), wx.BRUSHSTYLE_SOLID)
        return get_white_background_brush()

    def GetLines(self):
        return self._lines

    def Delete(self):
        """
        Fully disconnect this shape from parents, children, the
        canvas, etc.
        """
        # if self._parent:
        #     self._parent.GetChildren().remove(self)
        #
        # for child in self.GetChildren():
        #     child.Delete()
        #
        # ANDY: don't worry about the node edge, that is taken care of elsewhere

        self.ClearText()
        self.ClearRegions()
        self.ClearAttachments()

        # self._handlerShape = None

        if self._canvas:
            # self.RemoveFromCanvas(self._canvas)
            self._canvas.DeleteShape(self)  # ogllike

        # if self.GetEventHandler():
        #     self.GetEventHandler().OnDelete()
        self._eventHandler = None

    def ClearAttachments(self):
        """Clear internal custom attachment point shapes (of class
        :class:`~lib.ogl.AttachmentPoint`)
        """
        self._attachmentPoints = []

    def ClearText(self, regionId=0):
        """
        Clear the text from the specified text region.

        :param `regionId`: the region identifier

        """
        if regionId == 0:
            self._text = ""
        if regionId < len(self._regions):
            self._regions[regionId].ClearText()

    def Erase(self, dc):
        """
        Erase the shape.

        Does not repair damage caused to other shapes.
        """
        # self.GetEventHandler().OnErase(dc)
        # self.GetEventHandler().OnEraseControlPoints(dc)
        # self.GetEventHandler().OnDrawBranches(dc, erase = True)

    def EraseContents(self, dc):
        """
        Erase the shape contents, that is, the area within the shape's
        minimum bounding box.
        """
        # self.GetEventHandler().OnEraseContents(dc)

    def move_to(self, topx, lefty):  # ANDY ADDED - moves directly to pure top left, e.g. 0,0
        x = (0 - self.x[0]) + topx
        y = (0 - self.y[0]) + lefty
        self.x = list(map((lambda v: v + x), self.x))
        self.y = list(map((lambda v: v + y), self.y))

    def move_center(self, x, y):  # ANDY ADDED - moves centre to x,y
        delta_x = x - self._xpos
        delta_y = y - self._ypos
        self.move(delta_x, delta_y)

    # def Move(self, dc, topx, lefty, display):
    #     # self.move(topx, lefty) - no, this does a relative delta move
    #     self.move_to(topx, lefty)  # NEW

    def Move(self, dc, x, y, display=True):
        """
        Move the shape to the given position.

        :param `dc`: the device context
        :param `x`: the x position of the shape's **centre**
        :param `y`: the y position of the shape's **centre**
        :param `display`: if `True` redraw

        Use :meth:`MoveTo` when working with top-left coordinates.

        """
        # old_x = self._xpos
        # old_y = self._ypos
        #
        # if not self.GetEventHandler().OnMovePre(dc, x, y, old_x, old_y, display):
        #     return
        #
        # self._xpos, self._ypos = x, y
        self.move_center(x, y)  # NEW

        self.ResetControlPoints()

        # if display:
        #     self.Draw(dc)
        # self.draw(dc)  # INVALID dc if we do this

        self.MoveLinks(dc)
        #
        # self.GetEventHandler().OnMovePost(dc, x, y, old_x, old_y, display)

    def MoveTo(self, dc, x, y, display=True):
        """Move the shape so its top-left corner is at ``(x, y)``.

        Unlike :meth:`Move`, which takes the centre position, this matches the
        coordinate convention used by layouts and diagram persistence.  Attached
        lines are refreshed via :meth:`MoveLinks`.

        :param `dc`: the device context (may be ``None``)
        :param `x`: the x position of the shape's top-left corner
        :param `y`: the y position of the shape's top-left corner
        :param `display`: accepted for compatibility; drawing is left to the caller
        """
        self.move_to(x, y)
        self.ResetControlPoints()
        self.MoveLinks(dc)

    def MoveLinks(self, dc):
        """Redraw all the lines attached to the shape."""
        # self.GetEventHandler().OnMoveLinks(dc)
        self.OnMoveLinks(dc)  # ANDY

    def OnMoveLinks(self, dc):
        """The move links handler."""
        # if self._previousHandler:
        #     self._previousHandler.OnMoveLinks(dc)

    def ResetControlPoints(self):
        """Shape, RectangleShape, CommentShape(RectangleShape) all didn't have this method
        so I defined it here, doing nothing, to stop failed calls to it."""

    def SetCanvas(self, theCanvas):
        """
        Set the canvas, identical to Shape.Attach.

        :param `theCanvas`: an instance of :class:`~lib.ogl.Canvas`

        """
        self._canvas = theCanvas
        # for shape in self._children:
        #     shape.SetCanvas(theCanvas)

    def GetCanvas(self):
        """Get the internal canvas."""
        return self._canvas

    def Show(self, show):
        """Set whether this shape (and any composite children) is drawn."""
        self._visible = show
        for child in getattr(self, "_compositeChildren", []) or []:
            child.Show(show)

    def IsShown(self):
        """Return True when this shape is in a visible state."""
        return getattr(self, "_visible", True)

    def GetParent(self):
        """Get the parent of this shape, if it is part of a composite."""
        # return self._parent
        return None

    def SetParent(self, p):
        """Set the parent

        :param `p`: the parent

        """
        # self._parent = p

    # Get the top - most (non-division) ancestor, or self
    def GetTopAncestor(self):
        """
        Return the top-most ancestor of this shape (the root of
        the composite).
        """
        # if not self.GetParent():
        #     return self
        #
        # if isinstance(self.GetParent(), DivisionShape):
        #     return self
        # return self.GetParent().GetTopAncestor()
        return self

    def GetPerimeterPoint(self, x1, y1, x2, y2):
        """
        Get the point at which the line from (x1, y1) to (x2, y2) hits
        the shape.

        :param `x1`: the x1 position
        :param `y1`: the y1 position
        :param `x2`: the x2 position
        :param `y2`: the y2 position

        :returns: `False` if the line doesn't hit the perimeter.

        """
        return False


class LineShapeBase(Shape):
    def __init__(self, x1=0, y1=0, x2=0, y2=0):
        Shape.__init__(self, [x1, x2], [y1, y2])

    def draw(self, dc):
        Shape.draw(self, dc)
        dc.DrawLine(
            int(self.x[0]), int(self.y[0]), int(self.x[1]), int(self.y[1])
        )  # python 3.10 needs ints
        # print("DrawLine", self.x[0], self.y[0], self.x[1], self.y[1])

    def HitTest(self, x, y):
        if x < min(self.x) - 3:
            return False
        if x > max(self.x) + 3:
            return False
        if y < min(self.y) - 3:
            return False
        if y > max(self.y) + 3:
            return False

        top = (x - self.x[0]) * (self.x[1] - self.x[0]) + (y - self.y[0]) * (self.y[1] - self.y[0])
        distsqr = pow(self.x[0] - self.x[1], 2) + pow(self.y[0] - self.y[1], 2)
        u = float(top) / float(distsqr)

        newx = self.x[0] + u * (self.x[1] - self.x[0])
        newy = self.y[0] + u * (self.y[1] - self.y[0])

        dist = pow(pow(newx - x, 2) + pow(newy - y, 2), 0.5)

        if dist > 7:
            return False
        return True


class RectangleShape(Shape):
    def __init__(self, x=20, y=20, x2=90, y2=90):
        # ANDY
        super().__init__([x, x2], [y, y2])
        # print("RectangleShape created request was ", x, y, x2, y2, "resulting coords are", self.x, self.y)
        self.sanity()

        # in wx ogl this is in the Shape class - but I don't want that class to be too heavy
        # so I put it here, but then again the regions are defined on the Shape class...
        #
        # Set up a default region. Much of the above will be put into
        # the region eventually (the duplication is for compatibility)
        region = ShapeRegion()
        region.SetName("0")
        region.SetFont(
            wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )  # NormalFont)
        region.SetFormatMode(FORMAT_CENTRE_HORIZ | FORMAT_CENTRE_VERT)
        region.SetColour("BLACK")
        self._regions.append(region)

        # ANDY ADDED
        self._font = None  # set in the next line
        self.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        # NormalFont - doesn't exist till ogl initialised is called, so useless here
        # wx.Font(14, wx.MODERN, wx.NORMAL, wx.NORMAL, False) # ANDY ADDED
        # wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self._attachmentMode = ATTACHMENT_MODE_NONE

        self._formatted = False

    @property
    def _width(self):
        width, height = self.GetBoundingBoxMin()
        return width

    @_width.setter
    def _width(self, value):
        # self.x[1] = self.x[0] + value  # OLD
        self.x = [self._xpos - value / 2, self._xpos + value / 2]  # NEW, assumes square shape
        assert len(self.x) == 2

    @property
    def _height(self):
        width, height = self.GetBoundingBoxMin()
        return height

    @_height.setter
    def _height(self, value):
        # self.y[1] = self.y[0] + value  # OLD
        self.y = [self._ypos - value / 2, self._ypos + value / 2]  # NEW, assumes square shape
        assert len(self.y) == 2

    def SetFont(self, the_font):  # ANDY ADDED
        self._font = the_font

    def AddText(self, string):
        """Add a line of text to the shape's default text region."""
        if not self._regions:
            return

        region = self._regions[0]
        # region.ClearText()  # TODO somehow clears all except last line in a comment shape?
        new_line = ShapeTextLine(0, 0, string)
        text = region.GetFormattedText()
        text.append(new_line)

        self._formatted = False

    def OnDrawContents(self, dc):
        """The draw contents handler."""
        if not self._regions:
            return

        bound_x, bound_y = self.GetBoundingBoxMin()

        if self._pen:
            dc.SetPen(self._pen)

        for region in self._regions:
            if region.GetFont():
                dc.SetFont(region.GetFont())

            dc.SetTextForeground(region.GetActualColourObject())
            dc.SetBackgroundMode(wx.TRANSPARENT)
            if not self._formatted:
                CentreText(
                    dc,
                    region.GetFormattedText(),
                    self._xpos,
                    self._ypos,
                    bound_x - 2 * self._textMarginX,
                    bound_y - 2 * self._textMarginY,
                    region.GetFormatMode(),
                )
                self._formatted = True

            if not self.GetDisableLabel():
                DrawFormattedText(
                    dc,
                    region.GetFormattedText(),
                    self._xpos,
                    self._ypos,
                    bound_x - 2 * self._textMarginX,
                    bound_y - 2 * self._textMarginY,
                    region.GetFormatMode(),
                )

    def GetDisableLabel(self):
        return False

    def sanity(self):
        # ANDY ADDED SAFEGUARD
        assert self.x[1] >= self.x[0], f"RectangleShape has negative shape in x dimention: {self.x}"
        assert self.y[1] >= self.y[0], f"RectangleShape has negative shape in y dimention: {self.y}"

    def draw(self, dc):
        Shape.draw(self, dc)
        dc.DrawRectangle(
            int(self.x[0]),
            int(self.y[0]),
            int(self.x[1] - self.x[0]),
            int(self.y[1] - self.y[0]),  # python 3.10 needs ints - already was here
        )

    def OnDraw(self, dc):
        """Use the draw handler instead - avoid recursion mishaps calling both."""
        pass

    def HitTest(self, x, y):
        self.sanity()
        if x < self.x[0]:
            return False
        if x > self.x[1]:
            return False
        if y < self.y[0]:
            return False
        if y > self.y[1]:
            return False
        return True

    # ANDY EXTRAS

    def GetBoundingBoxMin(self):
        """Get the bounding box minimum."""
        # return self._width, self._height
        # Re-implement rectangle bounding box to use .x.y point lists directly
        width = abs(self.x[1] - self.x[0])
        height = abs(self.y[1] - self.y[0])
        return width, height

    def SetSize(self, x, y, recursive=False):
        """
        Set the size.

        :param `x`: the width
        :param `y`: the height
        :param `recursive`: not used

        """
        # print("setting the size of the rectangle", x, y)
        self.SetAttachmentSize(x, y)
        self._width = max(x, 1)
        self._height = max(y, 1)
        self.SetDefaultRegionSize()

    # def OnMotion(self, event):  # ANDY invented event, now in shape - previously only in canvas and not transmitted to shape
    #     print("OnMotion rectangle shape")
    #     if self._dragState == StartDraggingLeft:  # used to be a canvas thing, ANDY made it shape level
    #         self._dragState = ContinueDraggingLeft
    #
    # def OnMove(self, event):  # never gets called - do we need to bind?
    #     print("OnMove rectangle shape")

    def ClearRegions(self):
        """Clear the ShapeRegions from the shape."""
        self._regions = []

    def AddRegion(self, region):
        """Add a region to the shape."""
        self._regions.append(region)

    def GetRegions(self):
        """Get the list of ShapeRegions."""
        return self._regions

    def SetDefaultRegionSize(self):
        """Set the default region to be consistent with the shape size."""
        # if not self._regions:
        #     return
        # w, h = self.GetBoundingBoxMax()
        # self._regions[0].SetSize(w, h)

    def SetAttachmentSize(self, w, h):
        """
        Set the attachment size.

        :param `w`: width
        :param `h`: height

        """
        width, height = self.GetBoundingBoxMin()
        if width == 0:
            scaleX = 1.0
        else:
            scaleX = float(w) / width
        if height == 0:
            scaleY = 1.0
        else:
            scaleY = float(h) / height

        for point in self._attachmentPoints:
            point._x = point._x * scaleX
            point._y = point._y * scaleY

    def MoveLinks(self, dc):
        """Redraw all the lines attached to the shape."""
        # self.GetEventHandler().OnMoveLinks(dc)
        self.OnMoveLinks(dc)  # ANDY

    def OnMoveLinks(self, dc):
        """The move links handler."""
        # Want to set the ends of all attached links
        # to point to / from this object

        for line in self._lines:
            # line.GetEventHandler().OnMoveLink(dc)
            line.OnMoveLink(dc)  # ANDY

    def SetCentreResize(self, cr):
        """
        Specify whether the shape is to be resized from the centre (the
        centre stands still) or from the corner or side being dragged (the
        other corner or side stands still).
        """
        self._centreResize = cr

    def GetCentreResize(self):
        """
        `True` if the shape is to be resized from the centre (the centre stands
        still), or `False` if from the corner or side being dragged (the other
        corner or side stands still)

        """
        return self._centreResize

    def SetDraggable(self, drag, recursive=False):
        """Set the shape to be draggable or not draggable.

        :param `drag`: if `True` make shape draggable
        :param `recursive`: if `True` recurse through children

        """

    # Format a text string according to the region size, adding
    # strings with positions to region text list

    def FormatText(self, dc, s, i=0):
        """
        Reformat the given text region; defaults to formatting the
        default region.

        :param `dc`: the device contexr
        :param str `s`: the text string
        :param int `i`: the region identifier

        """
        self.ClearText(i)

        if not self._regions:
            return

        if i >= len(self._regions):
            return

        region = self._regions[i]
        region._regionText = s
        dc.SetFont(region.GetFont())

        w, h = region.GetSize()

        stringList = FormatText(
            dc, s, (w - 2 * self._textMarginX), (h - 2 * self._textMarginY), region.GetFormatMode()
        )
        for s in stringList:
            line = ShapeTextLine(0.0, 0.0, s)
            region.GetFormattedText().append(line)

        actualW = w
        actualH = h
        # Don't try to resize an object with more than one image (this
        # case should be dealt with by overriden handlers)
        if (
            (region.GetFormatMode() & FORMAT_SIZE_TO_CONTENTS)
            and len(region.GetFormattedText())
            and len(self._regions) == 1
            and not Shape.GraphicsInSizeToContents
        ):
            actualW, actualH = GetCentredTextExtent(dc, region.GetFormattedText())
            if actualW + 2 * self._textMarginX != w or actualH + 2 * self._textMarginY != h:
                # If we are a descendant of a composite, must make sure
                # the composite gets resized properly

                topAncestor = self.GetTopAncestor()
                if topAncestor != self:
                    Shape.GraphicsInSizeToContents = True

                    composite = topAncestor
                    composite.Erase(dc)
                    self.SetSize(actualW + 2 * self._textMarginX, actualH + 2 * self._textMarginY)
                    self.Move(dc, self._xpos, self._ypos)
                    composite.CalculateSize()
                    if composite.Selected():
                        composite.DeleteControlPoints(dc)
                        composite.MakeControlPoints()
                        composite.MakeMandatoryControlPoints()
                    # Where infinite recursion might happen if we didn't stop it
                    composite.Draw(dc)
                    Shape.GraphicsInSizeToContents = False
                else:
                    self.Erase(dc)

                self.SetSize(actualW + 2 * self._textMarginX, actualH + 2 * self._textMarginY)
                self.Move(dc, self._xpos, self._ypos)
                self.EraseContents(dc)
        CentreText(
            dc,
            region.GetFormattedText(),
            self._xpos,
            self._ypos,
            actualW - 2 * self._textMarginX,
            actualH - 2 * self._textMarginY,
            region.GetFormatMode(),
        )
        self._formatted = True

    def AddLine(self, line, other, attachFrom=0, attachTo=0, positionFrom=-1, positionTo=-1):
        """
        Add a line between this shape and the given other shape, at the
        specified attachment points.

        :param `line`: the line an instance of :class:`~lib.ogl.LineShape`
        :param `other`: the other shape, an instance of :class:`Shape`
        :param `attachFrom`: the attachment from point ???
        :param `attachTo`: the attachment to point ???
        :param `positionFrom`: the from position
        :param `positionTo`: the to position

        :note: The position in the list of lines at each end can also be
         specified, so that the line will be drawn at a particular point on
         its attachment point.

        """
        if positionFrom == -1:
            if line not in self._lines:
                self._lines.append(line)
        else:
            # Don't preserve old ordering if we have new ordering instructions
            try:
                self._lines.remove(line)
            except ValueError:
                pass
            if positionFrom < len(self._lines):
                self._lines.insert(positionFrom, line)
            else:
                self._lines.append(line)

        if positionTo == -1:
            if other not in other._lines:
                other._lines.append(line)
        else:
            # Don't preserve old ordering if we have new ordering instructions
            try:
                other._lines.remove(line)
            except ValueError:
                pass
            if positionTo < len(other._lines):
                other._lines.insert(positionTo, line)
            else:
                other._lines.append(line)

        line.SetFrom(self)
        line.SetTo(other)
        line.SetAttachments(attachFrom, attachTo)

        dc = wx.MemoryDC()
        # dc.SelectObject(self.GetCanvas().GetBuffer())
        # self.GetCanvas().PrepareDC(dc)
        self.MoveLinks(dc)

    def RemoveLine(self, line):
        """
        Remove the given line from the shape's list of attached lines.

        :param `line`: an instance of :class:`~lib.ogl.LineShape`

        """
        # if line.GetFrom() == self:
        #     line.GetTo()._lines.remove(line)
        # else:
        #     line.GetFrom()._lines.remove(line)
        #
        # self._lines.remove(line)

    def SetAttachmentMode(self, mode):
        """
        Set the attachment mode.

        :param `mode`: if `True` attachment points will be significant when
         drawing lines to and from this shape. If `False` lines will be drawn
         as if to the centre of the shape.

        """
        self._attachmentMode = mode

    def GetAttachmentMode(self):
        """
        Get the attachment mode.

        See :meth:`Shape.SetAttachmentMode`
        """
        return self._attachmentMode

    # Assume (x1, y1) is centre of box (most generally, line end at box)
    def GetPerimeterPoint(self, x1, y1, x2, y2):  # ANDY NOTE - overrides Shape method
        """
        Get the perimeter point.

        :param `x1`: ???
        :param `y1`: ???
        :param `x2`: ???
        :param `y2`: ???

        """
        bound_x, bound_y = self.GetBoundingBoxMax()
        return FindEndForBox(bound_x, bound_y, self._xpos, self._ypos, x2, y2)


class PointShape(Shape):
    def __init__(self, x=20, y=20, size=4, type="rect"):
        Shape.__init__(self, [x], [y])
        self.type = type
        self.size = size
        if self.type == "rect":
            self.graphic = RectangleShape(x - size, y - size, x + size, y + size)
        self.graphic.pen = self.pen
        self.graphic.fill = self.fill

    def moveto(self, x, y):
        self.x = x
        self.y = y
        size = self.size
        self.graphic.x = [x - size, x + size]
        self.graphic.y = [y - size, y + size]

    def move(self, x, y):
        # self.x and self.y are lists of x coords and y coords
        # in the case of default PointShape that list only has one member
        print("MOVE MOVE MOVE MOVE" * 20)
        assert False, "when does this code get run?"
        if len(self.x) == 1:  # was self.x == 1:  which I think I added and is a typo # ANDY
            assert False
            # Simpler to understand code
            self.x[0] += x
            self.y[0] += y
        else:
            # Future possibility (original code)
            self.x = list(map((lambda v: v + x), self.x))  # add x to each member of list self.x
            self.y = list(map((lambda v: v + y), self.y))  # add y to each member of list self.y
        self.graphic.move(x, y)

    def HitTest(self, x, y):
        return self.graphic.HitTest(x, y)

    def draw(self, dc):
        self.graphic.pen = self.pen
        self.graphic.fill = self.fill
        self.graphic.draw(dc)


# ---------------------------------------------------------------------------------------------------------------


class ShapeCanvas(ScrolledWindow):
    # Zoom configuration.  Both are class attributes, so a subclass can tune them
    ZOOM_MIN_SCALE = 0.3
    ZOOM_MAX_SCALE = 5.0
    ZOOM_STEP = 0.25
    ZOOM_WHEEL_STEP = 0.05  # fine step used by Ctrl+mousewheel
    ZOOM_ANCHOR_MOUSE = "mouse"
    ZOOM_ANCHOR_SELECTION = "selection"
    ZOOM_ANCHOR_CENTER = "center"
    #: bounds margin (px) added to the virtual canvas size
    CANVAS_MARGIN = 20
    #: pixels scrolled per wheel notch (wx already reports the OS scroll direction)
    WHEEL_SCROLL_PIXELS = 20
    #: pixels of movement before a canvas drag becomes a pan
    PAN_START_THRESHOLD = 3
    #: pixels of movement before a shape drag/resize starts (classic OGL uses 3)
    DRAG_TOLERANCE = 3
    #: raise a shape to the top when it is clicked
    bringClickedShapeToFront = True
    #: what a plain left-drag on empty canvas does: draw a marquee or pan
    EMPTY_DRAG_PAN = "pan"
    EMPTY_DRAG_MARQUEE = "marquee"
    emptyDragMode = EMPTY_DRAG_MARQUEE
    #: marquee selects shapes it touches; False would require full containment
    marqueeSelectsTouching = True
    MARQUEE_MIN_SIZE = 3
    #: snap shape drags to the diagram grid
    snapToGrid = False
    #: draw the diagram grid in the background
    showGrid = False
    #: while dragging, snap to other shapes' edges/centres and draw guides
    alignmentGuides = True
    #: alignment guide tolerance in screen pixels
    ALIGN_TOLERANCE = 4
    #: use AutoBufferedPaintDC to reduce flicker on platforms that do not composite
    bufferedPainting = False
    UNDO_LIMIT = 50

    def __init__(self, parent, id=-1, pos=(-1, -1), size=(-1, -1), style=0, name=""):
        ScrolledWindow.__init__(self, parent, id, pos, size, style, name)
        if self.bufferedPainting:
            # With BG_STYLE_PAINT the canvas is responsible for erasing.
            self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetScrollbars(1, 1, 1000, 800)
        self.diagram = None
        self.nodes = []
        self.currentPoint = [0, 0]  # x and y of last mouse click or mouse drag
        self.selectedShapes = []
        self._hover_shape = None  # shape whose ports are shown as drag targets
        self.scalex = 1.0
        self.scaley = 1.0
        self._scroll_remainder = 0.0  # fractional wheel scrolling for trackpads
        self.defaultKeyBindings = True
        #: automatically recalculate the virtual size after shapes change
        self.autoVirtualSize = True
        #: where each zoom call anchors by default: mouse / selection / center
        self.zoomAnchor = self.ZOOM_ANCHOR_MOUSE
        #: when False, Ctrl+wheel and drag-to-pan are not bound to the mouse wheel/drag
        self.zoomInputEnabled = True
        self.panOnDrag = True
        self.duplicateKeyEnabled = True
        self.nudgeKeysEnabled = True
        self._space_down = False
        self._marquee_active = False
        self._marquee_start = (0, 0)
        self._marquee_current = (0, 0)
        self._marquee_additive = False
        self._marquee_base = []
        self.undoKeyBindings = True
        self._undo_stack = []
        self._redo_stack = []
        self._undo_pending = None
        self._undo_depth = 0
        self._restoring_state = False
        # cache + guard for the virtual size calculations
        self._bounds_cache = None
        self._in_resize = False

        # Window Events
        self.Bind(EVT_PAINT, self.onPaintEvent)  # was EVT_PAINT(self, self.onPaintEvent)
        # Mouse Events
        self.Bind(EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(EVT_LEFT_DCLICK, self.OnLeftDClick)

        self.Bind(EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(EVT_RIGHT_DCLICK, self.OnRightDClick)

        self.Bind(EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.Bind(wx.EVT_MAGNIFY, self.OnMagnify)  # macOS trackpad pinch
        self.Bind(wx.EVT_MIDDLE_DOWN, self._pan_begin)
        self.Bind(wx.EVT_MIDDLE_UP, self._pan_end)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self._capture_lost)
        # Key events: the default OnKeyDown implements Delete/Tab/Ctrl+A/Ctrl+C/Ctrl+V,
        # arrows, Esc, duplicate and z-order.
        self.Bind(EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(EVT_KEY_UP, self.OnKeyUp)

        # ANDY ADDED ###
        self._dragState = NoDragging
        self._draggedShape = None
        self._drag_free_aspect = False
        self._drag_from_center = False
        self._drag_start_client = None
        self._drag_started = False
        self._drag_start_hull = None
        self._drag_origin_diagram = (0.0, 0.0)
        self._dragging_resize_node = None
        self._guides = []
        self.gridColour = wx.Colour(228, 228, 228)
        self.guideColour = wx.Colour(200, 60, 200)
        ####

    def _bounds_changed(self):
        """Refresh the virtual size after shapes were added, moved or deleted."""
        self.invalidate_bounds_cache()
        if getattr(self, "autoVirtualSize", True):
            self._apply_scrollbars()

    def _attach_canvas(self, shape):
        """Attach this canvas to a shape and everything the shape owns.

        OGLlike only ever attached the canvas in AddShape/AppendShape, so shapes
        inserted with InsertShape (and their children) had ``_canvas is None``.
        Everything that needs to know its canvas (mouse handling, selection
        nodes, link updates) now goes through this one helper.
        """

        def visit(node, seen):
            if id(node) in seen:
                return
            seen.add(id(node))
            node.SetCanvas(self)
            for child in getattr(node, "_compositeChildren", None) or []:
                visit(child, seen)
            # Shapes that own a nested set of shapes expose it as .shapes.
            for child in getattr(node, "shapes", None) or []:
                visit(child, seen)

        visit(shape, set())

    def AddShape(self, shape, addAfter=None):
        self._attach_canvas(shape)
        self.diagram.AddShape(shape, addAfter)
        self._bounds_changed()

    def AppendShape(self, shape):
        self._attach_canvas(shape)
        self.diagram.AppendShape(shape)
        self._bounds_changed()

    def InsertShape(self, shape, index=0):
        self._attach_canvas(shape)
        self.diagram.InsertShape(shape, index)
        self._bounds_changed()

    def DeleteShape(self, shape):
        self.diagram.DeleteShape(shape)
        self._bounds_changed()

    def RemoveShape(self, shape):
        self.diagram.DeleteShape(shape)
        self._bounds_changed()

    def delete_selected(self):
        """Delete every selected shape as one undoable operation."""
        shapes = list(self.getSelectedShapes())
        if not shapes:
            return
        self.begin_undo()
        try:
            for shape in shapes:
                try:
                    self.diagram.DeleteShape(shape)
                except ValueError:
                    pass
            self.deselect()
            self._bounds_changed()
        finally:
            self.commit_undo()
        self.Refresh()

    @staticmethod
    def _ctrl(event):
        # CmdDown() is Command on macOS and Control elsewhere.
        return event.ControlDown() or event.CmdDown()

    def OnKeyDown(self, event):
        """Default key handling.  Subclasses may override this, but should remember
        to call ``event.Skip()`` when the key is not handled."""
        if not self.defaultKeyBindings:
            event.Skip()
            return
        key = event.GetKeyCode()

        if key == wx.WXK_SPACE:
            self._space_down = True
            event.Skip()
            return
        if key == wx.WXK_ESCAPE:
            self.deselect()
            self.Refresh()
            return

        if key in (wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_UP, wx.WXK_DOWN) and self.nudgeKeysEnabled:
            step = 10 if event.ShiftDown() else 1
            dx = -step if key == wx.WXK_LEFT else step if key == wx.WXK_RIGHT else 0
            dy = -step if key == wx.WXK_UP else step if key == wx.WXK_DOWN else 0
            self.nudge_selected(dx, dy)
        elif key in (wx.WXK_DELETE, 127):  # DELETE
            self.delete_selected()
        elif key == 9:  # TAB
            shapes = getattr(self.diagram, "shapes", []) if self.diagram else []
            if not shapes:
                return
            current = self.getSelectedShapes()
            if current:
                index = shapes.index(current[0]) if current[0] in shapes else -1
                self.deselect()
                self.select(shapes[(index + 1) % len(shapes)])
            else:
                self.select(shapes[0])
        elif key == 65 and self._ctrl(event):  # CTRL-A
            for s in getattr(self.diagram, "shapes", []):
                self.select(s)
        elif key == 67 and self._ctrl(event):  # CTRL-C
            del clipboard[:]
            clipboard.extend(self.getSelectedShapes())
        elif key == 86 and self._ctrl(event):  # CTRL-V
            self.begin_undo()
            try:
                for i in clipboard:
                    self.AddShape(i.Copy())
                self._bounds_changed()
            finally:
                self.commit_undo()
        elif key == 68 and self._ctrl(event):  # CTRL-D
            if self.duplicateKeyEnabled and not event.ShiftDown():
                self.duplicate_selected()
            elif event.ShiftDown():  # CTRL-SHIFT-D - debug info
                pt = GetMousePosition()
                mouseX = pt[0] - self.GetScreenPosition().x
                mouseY = pt[1] - self.GetScreenPosition().y
                print("%s,%s %s" % (mouseX, mouseY, self.shapeFromPoint((mouseX, mouseY))))
            else:
                event.Skip()
        elif self.undoKeyBindings and key == 90 and self._ctrl(event):  # CTRL-Z
            if event.ShiftDown():
                self.redo()
            else:
                self.undo()
        elif self.undoKeyBindings and key == 89 and self._ctrl(event):  # CTRL-Y
            self.redo()
        else:
            event.Skip()
            self.Refresh()
            return
        self.Refresh()

    def OnKeyUp(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            self._space_down = False
        event.Skip()

    def onPaintEvent(self, event):
        dc = (wx.AutoBufferedPaintDC if self.bufferedPainting else PaintDC)(self)
        if self.bufferedPainting:
            # BG_STYLE_PAINT: nothing erases the background for us.
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
        self.PrepareDC(dc)
        dc.SetUserScale(self.scalex, self.scaley)
        self._apply_content_origin(dc)
        self._draw_grid(dc)
        # for item in self.diagram.shapes + self.nodes:
        #     item.draw(dc)
        self.Redraw(dc)  # does the above two lines
        self._draw_guides(dc)
        self._draw_marquee(dc)

    def _apply_content_origin(self, dc):
        """Shift drawing so content at negative coordinates stays on canvas.

        Scroll offsets cannot go negative, so the scroll origin is the content's
        top-left corner (``getContentOrigin``) rather than diagram (0, 0).
        """
        min_x, min_y = self._content_rect()[:2]
        if min_x or min_y:
            scroll_x, scroll_y = self._scroll_offset_pixels()
            dc.SetDeviceOrigin(
                -int(scroll_x + min_x * self.scalex),
                -int(scroll_y + min_y * self.scaley),
            )

    def OnRightDown(self, event):
        # ANDY
        shape = self.getCurrentShape(event)
        if shape:
            # print("ogllike canvas OnRightDown on shape")
            shape.OnRightDown(event)

        # ANDY
        # if False and self.getCurrentShape(event):
        #     self.getCurrentShape(event).OnRightDown(event)

    def OnRightUp(self, event):
        # ANDY
        shape = self.getCurrentShape(event)
        if shape:
            shape.OnRightUp(event)

        # ANDY
        # if False and self.getCurrentShape(event):
        #     self.getCurrentShape(event).OnRightUp(event)
        # else:
        #     #
        #     self.shape_popup_menu_is_of = self.getCurrentShape(event)
        #     self.popupmenu = Menu()
        #     item = self.popupmenu.Append(2021, "Properties...")
        #     self.Bind(EVT_MENU, self.OnPopupItemSelected, item)
        #     item = self.popupmenu.Append(2022, "Delete Node")
        #     self.Bind(EVT_MENU, self.OnDelete, item)
        #     item = self.popupmenu.Append(2023, "Cancel")
        #     self.Bind(EVT_MENU, self.OnPopupItemSelected, item)
        #
        #     pos = event.GetPosition()
        #     # pos = self.ScreenToClient(pos)
        #     self.PopupMenu(self.popupmenu, pos)
        ########

    # ANDY

    def join_shapes(self, fromShape, toShape, edge_type="association"):
        """Connect two shapes with an attached line.

        The edge is a ``LineShape`` attached via ``AddLine`` (with the
        default attachment mode), so its endpoints are clipped to the shapes'
        perimeters on the centre-to-centre ray and are recomputed whenever
        either shape moves.  The edge therefore always leaves and enters
        through whichever sides face each other, from any direction.

        Port nodes are only the drag handles a connection is started from;
        they never constrain a finished edge.  ``edge_type`` is accepted for
        compatibility (subclasses such as pynsource's UmlCanvas override this
        to build richer edges) but the base line is unadorned.
        """
        from .lines import LineShape

        self.deselect()
        line = LineShape()
        line.MakeLineControlPoints(2)
        line.SetEnds(fromShape.GetX(), fromShape.GetY(), toShape.GetX(), toShape.GetY())
        self.InsertShape(line, 0)
        fromShape.AddLine(line, toShape)

    def Redraw(self, dc):
        """
        Draws all shapes to the dc.

        If the dc is via canvas.Refresh() -> EVT_PAINT -> self.onPaintEvent(dc) then
        the dc is a normal paint dc

        If the dc is via print preview, then its a dc for that purpose.

        Aside: This method existed in wx.ogl but not in core, since the core
        onPaintEvent() simply did the following loop itself.  But when we need to support
        drawing onto other dcs, like in the case of print preview, its better to
        refactor this loop out to here.

        Its annoyingly named similar to Refresh, so easy to confuse when to use each.
        Refresh is part of wxpython, whereas Redraw is made up.  The functionality
        of Redraw could just be put inside the onPaintEvent and Redraw deleted.
        """
        for item in self.diagram.shapes + self.nodes:
            if getattr(item, "IsShown", lambda: True)():
                item.draw(dc)

    def ExportPng(self, path, scale=1.0, margin=0):
        """Render the diagram to a PNG file and return True on success.

        Selection handles, guides and the marquee are not included.  ``scale``
        multiplies diagram units and ``margin`` adds a border in output pixels.
        """
        if self.diagram is None:
            return False
        shapes = [
            s for s in self.diagram.shapes if getattr(s, "IsShown", lambda: True)()
        ]
        xs = [value for shape in shapes for value in shape.x]
        ys = [value for shape in shapes for value in shape.y]
        if xs and ys:
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
        else:
            min_x = min_y = max_x = max_y = 0

        width = int(max(1, round((max_x - min_x) * scale)) + 2 * margin)
        height = int(max(1, round((max_y - min_y) * scale)) + 2 * margin)
        bitmap = wx.Bitmap(width, height)
        dc = wx.MemoryDC(bitmap)
        try:
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
            dc.SetUserScale(scale, scale)
            dc.SetDeviceOrigin(int(margin - min_x * scale), int(margin - min_y * scale))
            for shape in shapes:
                shape.draw(dc)
        finally:
            dc.SelectObject(wx.NullBitmap)
        return bool(bitmap.SaveFile(str(path), wx.BITMAP_TYPE_PNG))

    ################

    def OnRightDClick(self, event):
        if self.getCurrentShape(event):
            self.getCurrentShape(event).OnRightDClick(event)

    def OnLeftDClick(self, event):
        if self.getCurrentShape(event):
            self.getCurrentShape(event).OnLeftDClick(event)

    # --- Undo / redo -------------------------------------------------------

    def snapshot_state(self):
        """Return a comparable snapshot of the diagram state.

        Applications with their own model can override this and restore_state()
        with an opaque snapshot object; the undo stack only compares snapshots
        for equality.
        """
        if self.diagram is None:
            return None
        shapes = tuple(self.diagram.shapes)
        geometry = tuple(
            (s, tuple(s.x), tuple(s.y), s.GetId(), s.IsShown()) for s in shapes
        )
        return {"shapes": shapes, "geometry": geometry}

    def restore_state(self, snapshot):
        """Restore a snapshot produced by snapshot_state()."""
        if snapshot is None or self.diagram is None:
            return
        self._restoring_state = True
        try:
            self.deselect()
            self.diagram.shapes[:] = list(snapshot["shapes"])
            for shape, x, y, shape_id, shown in snapshot["geometry"]:
                shape.x = list(x)
                shape.y = list(y)
                shape.SetId(shape_id)
                shape.Show(shown)
                self._attach_canvas(shape)
                if getattr(shape, "is_bitmap", False):
                    shape.SetSize(
                        max(1, int(abs(shape.x[1] - shape.x[0]))),
                        max(1, int(abs(shape.y[1] - shape.y[0]))),
                    )
                shape.MoveLinks(dc=None)
            self.invalidate_bounds_cache()
            self.update_virtual_size()
            self.Refresh()
        finally:
            self._restoring_state = False

    def begin_undo(self):
        """Start a logical undoable operation (nesting is allowed)."""
        if self._restoring_state:
            return
        if self._undo_depth == 0:
            self._undo_pending = self.snapshot_state()
        self._undo_depth += 1

    def commit_undo(self):
        """Finish a logical undoable operation."""
        if self._restoring_state or self._undo_depth == 0:
            return
        self._undo_depth -= 1
        if self._undo_depth > 0:
            return
        before = self._undo_pending
        self._undo_pending = None
        if before is None:
            return
        after = self.snapshot_state()
        if after == before:
            return
        self._undo_stack.append(before)
        if len(self._undo_stack) > self.UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def clear_undo(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._undo_pending = None
        self._undo_depth = 0

    def canUndo(self):
        return bool(self._undo_stack)

    def canRedo(self):
        return bool(self._redo_stack)

    def undo(self):
        if not self._undo_stack:
            return False
        current = self.snapshot_state()
        previous = self._undo_stack.pop()
        self._redo_stack.append(current)
        self.restore_state(previous)
        return True

    def redo(self):
        if not self._redo_stack:
            return False
        current = self.snapshot_state()
        following = self._redo_stack.pop()
        self._undo_stack.append(current)
        self.restore_state(following)
        return True

    # --- Marquee selection -------------------------------------------------

    @staticmethod
    def _shape_bounds(shape):
        if not shape.x or not shape.y:
            return None
        return min(shape.x), min(shape.y), max(shape.x), max(shape.y)

    @staticmethod
    def _rect_intersects(a, b):
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    @staticmethod
    def _rect_contains(outer, inner):
        return (
            outer[0] <= inner[0]
            and outer[1] <= inner[1]
            and outer[2] >= inner[2]
            and outer[3] >= inner[3]
        )

    def _marquee_rect(self):
        x1, y1 = self._marquee_start
        x2, y2 = self._marquee_current
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

    def _marquee_begin(self, event):
        point = self.getEventCoordinates(event)
        self._marquee_active = True
        self._marquee_start = point
        self._marquee_current = point
        self._marquee_additive = event.ShiftDown() or self._ctrl(event)
        self._marquee_base = list(self.getSelectedShapes()) if self._marquee_additive else []
        if not self._marquee_additive:
            self.deselect()
        if not self.HasCapture():
            self.CaptureMouse()
        self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        self.Refresh()

    def _marquee_update(self, event):
        self._marquee_current = self.getEventCoordinates(event)
        self._apply_marquee_selection()
        self.Refresh()

    def _apply_marquee_selection(self):
        if self.diagram is None:
            return
        rect = self._marquee_rect()
        tiny = (
            abs(rect[2] - rect[0]) < self.MARQUEE_MIN_SIZE
            and abs(rect[3] - rect[1]) < self.MARQUEE_MIN_SIZE
        )
        matches = []
        if not tiny:
            for shape in self.diagram.shapes:
                if not getattr(shape, "IsShown", lambda: True)():
                    continue
                if not getattr(shape, "marqueeSelectable", True):
                    continue
                bounds = self._shape_bounds(shape)
                if bounds is None:
                    continue
                hit = (
                    self._rect_intersects(rect, bounds)
                    if self.marqueeSelectsTouching
                    else self._rect_contains(rect, bounds)
                )
                if hit:
                    matches.append(shape)

        wanted = (self._marquee_base if self._marquee_additive else []) + matches
        current = self.getSelectedShapes()
        if {id(s) for s in current} == {id(s) for s in wanted}:
            return
        self.deselect()
        for shape in wanted:
            self.select(shape)

    def _marquee_end(self):
        if not self._marquee_active:
            return
        self._marquee_active = False
        self._marquee_base = []
        if self.HasCapture():
            self.ReleaseMouse()
        self.SetCursor(wx.NullCursor)
        self.Refresh()

    def _draw_marquee(self, dc):
        if not self._marquee_active:
            return
        rect = self._marquee_rect()
        if (
            abs(rect[2] - rect[0]) < self.MARQUEE_MIN_SIZE
            and abs(rect[3] - rect[1]) < self.MARQUEE_MIN_SIZE
        ):
            return
        dc.SetPen(wx.Pen(wx.BLUE, 1, wx.PENSTYLE_SHORT_DASH))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(
            int(rect[0]), int(rect[1]), int(rect[2] - rect[0]), int(rect[3] - rect[1])
        )

    # --- Grid / snapping / alignment guides --------------------------------

    def _visible_diagram_rect(self):
        """Diagram-coordinate rectangle currently visible in the client area."""
        client_w, client_h = self.GetClientSize()
        left, top = self.client_pos_in_diagram_coords(0, 0)
        right, bottom = self.client_pos_in_diagram_coords(client_w, client_h)
        return left, top, right, bottom

    def _draw_grid(self, dc):
        if not self.showGrid or self.diagram is None:
            return
        spacing = self.diagram.GetGridSpacing()
        # Below a few pixels the grid is just noise (and slow) - skip it.
        if spacing <= 0 or spacing * self.scalex < 6:
            return
        left, top, right, bottom = self._visible_diagram_rect()
        dc.SetPen(wx.Pen(self.gridColour, 1))
        x = int(left // spacing) * spacing
        while x <= right:
            dc.DrawLine(int(x), int(top), int(x), int(bottom))
            x += spacing
        y = int(top // spacing) * spacing
        while y <= bottom:
            dc.DrawLine(int(left), int(y), int(right), int(y))
            y += spacing

    def _draw_guides(self, dc):
        if not self._guides:
            return
        left, top, right, bottom = self._visible_diagram_rect()
        dc.SetPen(wx.Pen(self.guideColour, 1, wx.PENSTYLE_SHORT_DASH))
        for orientation, coord in self._guides:
            if orientation == "v":
                dc.DrawLine(int(coord), int(top), int(coord), int(bottom))
            else:
                dc.DrawLine(int(left), int(coord), int(right), int(coord))

    def _snap_enabled(self):
        return bool(self.snapToGrid or (self.diagram is not None and self.diagram.GetSnapToGrid()))

    def Snap(self, x, y):
        """Snap a diagram coordinate to the grid (if snapping is enabled)."""
        if self.diagram is None or not self._snap_enabled():
            return x, y
        return self.diagram.Snap(x, y)

    @staticmethod
    def _hull(shapes):
        xs = [value for shape in shapes for value in shape.x]
        ys = [value for shape in shapes for value in shape.y]
        return min(xs), min(ys), max(xs), max(ys)

    @staticmethod
    def _best_alignment(low, high, candidate_values, tolerance):
        """Return ``(offset, guide)`` for the nearest aligned edge or centre."""
        best_offset = None
        best_guide = None
        for other in candidate_values:
            for dragged in (low, (low + high) / 2.0, high):
                offset = other - dragged
                if abs(offset) <= tolerance and (
                    best_offset is None or abs(offset) < abs(best_offset)
                ):
                    best_offset = offset
                    best_guide = other
        return (best_offset or 0.0), best_guide

    def _snap_drag(self, shapes, start_hull, dx, dy):
        """Adjust a group drag for the grid and alignment guides.

        ``dx``/``dy`` are the cumulative drag delta since the mouse went down,
        and ``start_hull`` is the selection's hull at that moment.  Working from
        the total offset (rather than per-event deltas) means a shape is not
        stuck to a guide while the pointer keeps moving away from it.

        Returns the adjusted total delta and records guide lines for
        :meth:`_draw_guides`.
        """
        self._guides = []
        left, top, right, bottom = start_hull
        proposed_left = left + dx
        proposed_top = top + dy
        left, top = proposed_left, proposed_top
        right += dx
        bottom += dy

        if self._snap_enabled():
            left, top = self.Snap(left, top)

        if self.alignmentGuides and self.diagram is not None:
            tolerance = self.ALIGN_TOLERANCE / max(self.scalex, 1e-9)
            candidate_x = []
            candidate_y = []
            for other in self.diagram.shapes:
                if other in shapes or not isinstance(other, RectangleShape):
                    continue
                if len(other.x) < 2 or len(other.y) < 2:
                    continue
                candidate_x.extend((other.x[0], (other.x[0] + other.x[1]) / 2.0, other.x[1]))
                candidate_y.extend((other.y[0], (other.y[0] + other.y[1]) / 2.0, other.y[1]))
            offset_x, guide_x = self._best_alignment(left, right, candidate_x, tolerance)
            offset_y, guide_y = self._best_alignment(top, bottom, candidate_y, tolerance)
            left += offset_x
            top += offset_y
            if guide_x is not None:
                self._guides.append(("v", guide_x))
            if guide_y is not None:
                self._guides.append(("h", guide_y))

        return dx + (left - proposed_left), dy + (top - proposed_top)

    # --- Editing helpers ---------------------------------------------------

    def nudge_selected(self, dx, dy):
        """Move all selected shapes by dx,dy (no-op if nothing is selected)."""
        shapes = [s for s in self.getSelectedShapes() if not isinstance(s, Node)]
        if not shapes:
            return
        self.begin_undo()
        try:
            for shape in shapes:
                shape.move(dx, dy)
                shape.MoveLinks(dc=None)
            self.invalidate_bounds_cache()
            self.update_virtual_size()
            self.Refresh()
        finally:
            self.commit_undo()

    def duplicate_selected(self, offset=(20, 20)):
        """Copy selected top-level shapes and select the copies."""
        originals = [
            s
            for s in self.getSelectedShapes()
            if not isinstance(s, Node)
            and getattr(s, "_from", None) is None
            and getattr(s, "_to", None) is None
        ]
        if not originals:
            return []
        self.begin_undo()
        try:
            clones = []
            for shape in originals:
                clone = shape.Copy()
                clone.move(*offset)
                self.AddShape(clone)
                clones.append(clone)
            self.deselect()
            for clone in clones:
                self.select(clone)
            self.update_virtual_size()
            self.Refresh()
            return clones
        finally:
            self.commit_undo()

    def bring_to_front(self, shapes=None):
        """Move the given shapes (default: selection) to the top of the z-order."""
        shapes = list(shapes) if shapes is not None else list(self.getSelectedShapes())
        self.begin_undo()
        try:
            for shape in shapes:
                if self.diagram is not None and shape in self.diagram.shapes:
                    self.diagram.ChangeShapeOrder(shape, len(self.diagram.shapes) - 1)
            self.Refresh()
        finally:
            self.commit_undo()

    def send_to_back(self, shapes=None):
        """Move the given shapes (default: selection) to the bottom of the z-order."""
        shapes = list(shapes) if shapes is not None else list(self.getSelectedShapes())
        self.begin_undo()
        try:
            for shape in shapes:
                if self.diagram is not None and shape in self.diagram.shapes:
                    self.diagram.ChangeShapeOrder(shape, 0)
            self.Refresh()
        finally:
            self.commit_undo()

    def bring_forward(self, shapes=None):
        """Move the given shapes one step up in the z-order."""
        shapes = list(shapes) if shapes is not None else list(self.getSelectedShapes())
        self.begin_undo()
        try:
            for shape in shapes:
                if self.diagram is None or shape not in self.diagram.shapes:
                    continue
                index = self.diagram.shapes.index(shape)
                if index < len(self.diagram.shapes) - 1:
                    self.diagram.ChangeShapeOrder(shape, index + 1)
            self.Refresh()
        finally:
            self.commit_undo()

    def send_backward(self, shapes=None):
        """Move the given shapes one step down in the z-order."""
        shapes = list(shapes) if shapes is not None else list(self.getSelectedShapes())
        self.begin_undo()
        try:
            for shape in shapes:
                if self.diagram is None or shape not in self.diagram.shapes:
                    continue
                index = self.diagram.shapes.index(shape)
                if index > 0:
                    self.diagram.ChangeShapeOrder(shape, index - 1)
            self.Refresh()
        finally:
            self.commit_undo()

    def AddImage(
        self,
        path,
        max_size=None,
        center=True,
        send_to_back=True,
        shape_factory=None,
        **shape_kwargs,
    ):
        """Load an image, add it as a resizable bitmap shape and return it.

        ``max_size=(w, h)`` scales large images down (preserving aspect ratio).
        ``center=True`` places it in the middle of the current viewport.
        ``send_to_back=True`` puts imported images behind the diagram.
        ``shape_factory`` lets applications supply a shape subclass (for example
        one mixing in their own event handler).
        """
        from .bmpshape import ResizableBitmapShape

        image = wx.Image(path, wx.BITMAP_TYPE_ANY)
        if not image.IsOk():
            return None

        if max_size:
            max_w, max_h = max_size
            width, height = image.GetWidth(), image.GetHeight()
            if width and height:
                scale = min(1.0, float(max_w) / width, float(max_h) / height)
                if scale < 0.999:
                    image = image.Scale(
                        max(1, int(width * scale)),
                        max(1, int(height * scale)),
                        wx.IMAGE_QUALITY_HIGH,
                    )

        shape = shape_factory(**shape_kwargs) if shape_factory else ResizableBitmapShape()
        shape.SetBitmap(wx.Bitmap(image))
        shape.SetFilename(path)

        if center:
            client_w, client_h = self.GetClientSize()
            centre_x, centre_y = self.client_pos_in_diagram_coords(client_w / 2, client_h / 2)
            x = centre_x - image.GetWidth() / 2
            y = centre_y - image.GetHeight() / 2
        else:
            x = y = 0

        shape.move_to(x, y)
        self.AddShape(shape)
        if send_to_back:
            self.send_to_back([shape])
        self.Refresh()
        return shape

    def _capture_lost(self, event):
        self._panning = False
        self._pan_pending = False
        self._marquee_active = False
        self._marquee_base = []
        self.SetCursor(wx.NullCursor)

    def OnLeftDown(self, event):
        """If over a shape, selects the shape. Selecting the shape will create various Nodes
        attached to the shape, depending on whether it is Selectable, Resizable, Connectable etc.

        If shape is an ONode then a later OnMotion will thus send .move() to selected shapes which
        is just one selected ONode shape, thus ends up as ONode.move() which has code to initiate
        the line draw process, deselecting itself, the ONode, and selecting a newly create ConnectionLine,
        which then gets all subsequent OnMotion shape.move() calls.

        If shape is a normal rectangle shape then bring it to the front.
        If no shape, deselect all.
        """
        shape = self.getCurrentShape(event)
        # Remember where the drag started so tiny mouse tremors do not move or
        # resize anything (classic OGL waits DRAG_TOLERANCE pixels).
        self._drag_start_client = event.GetPosition() if hasattr(event, "GetPosition") else None
        self._drag_started = False
        self._drag_start_hull = None
        self._drag_origin_diagram = tuple(self.currentPoint)
        self._guides = []
        # Hover-shown ports have done their job once something is clicked:
        # the clicked node object is already in hand, so drop the hover set.
        self._clear_hover_ports()
        if DEBUG_DRAG:
            print("Master OnLeftDown over shape", shape)

        if shape is None:
            self._dragging_resize_node = None
            # Empty canvas: plain drag draws a marquee; Alt/Space/middle drag pans.
            pan_requested = self.panOnDrag and (
                event.AltDown() or getattr(self, "_space_down", False)
            )
            if pan_requested:
                self._pan_begin(event)
            elif self.panOnDrag and self.emptyDragMode == self.EMPTY_DRAG_PAN:
                self.deselect()
                self._pan_begin(event)
            else:
                self._marquee_begin(event)
            return

        if isinstance(shape, Node):
            # Clicking a resize/port handle must NOT clear self.nodes: those
            # are the visible handles.  Select just the node so OnMotion
            # resizes, while the other handles stay on screen.
            # Remember a resize handle so the resize can be finished on
            # mouse-up even if the pointer has moved away from the handle.
            self._dragging_resize_node = shape if isinstance(shape, ResizeableNode) else None
            self.begin_undo()
            self.select(shape)
            self.Refresh()
            return

        self._dragging_resize_node = None

        if self.bringClickedShapeToFront and not isinstance(shape, (Node, ConnectionShape)):
            # Bring normal shapes to top, not Node shapes or ConnectionShape lines
            self.diagram.ChangeShapeOrder(shape, len(self.diagram.shapes) - 1)

        # A click may become a drag or resize; record only if it changes state.
        self.begin_undo()
        shape.OnLeftDown(event)  # some shapes love this, Nodes and ConnectionShape don't implement

        # Deselect all other shapes before selecting the current shape, unless
        # shift/ctrl is down or the clicked shape is already part of the current
        # selection.  Keeping an existing multi-selection is what lets a drag
        # move the whole group.
        modifier = event.ShiftDown() or self._ctrl(event)
        already_selected = shape in self.getSelectedShapes()
        if not modifier and not already_selected:
            self.deselect()
        self.select(shape)  # will auto create various Nodes attached to points on the shape
        move_shapes = [s for s in self.getSelectedShapes() if not isinstance(s, Node)]
        self._drag_start_hull = self._hull(move_shapes) if move_shapes else None

        self.Refresh()

    def OnLeftUp(self, event):
        """When resizing a shape, getCurrentShape shape will be a ResizeableNode.

        When dragging a regular rectangle etc. shape, getCurrentShape shape will be that regular shape
            - also emit an OnEndDragLeft call, which simulates the wx.ogl equivalent.

        When dragging a line, selected shape is always a ConnectionShape
            - releasing over proper INode, shape will be INode (or ONode if dragging in reverse, from out to in)
            - releasing over "empty" canvas area, shape will be a ResizeableNode
        """
        if self._marquee_active:
            self._marquee_end()
            return
        if getattr(self, "_panning", False):
            self._pan_end()
            self.Refresh()
            return
        resize_node = self._dragging_resize_node
        self._dragging_resize_node = None
        self._drag_started = False
        self._guides = []
        try:
            # Hit-test before refreshing the bounds: moving content to negative
            # coordinates changes the scroll origin, and re-deriving it first
            # would move the mapping out from under this mouse-up.
            shape = self.getCurrentShape(event)
            self._bounds_changed()
            self._dump_drag_info("Master OnLeftUp", shape)
            if resize_node is not None:
                # A resize finishes even when the pointer has left the handle:
                # otherwise the node stayed selected and the handles looked
                # stuck after releasing away from the corner/edge.
                if shape is not None and shape is not resize_node:
                    if shape._canvas is None:
                        shape.SetCanvas(self)
                    shape.OnLeftUp(event)
                resize_node.leftUp(self.getSelectedShapes())
            elif shape:
                if shape._canvas is None:
                    # A shape can still arrive without a canvas (custom loaders,
                    # direct Diagram manipulation); repair instead of crashing
                    # halfway through mouse handling.
                    shape.SetCanvas(self)
                if self._dragState == ContinueDraggingLeft:
                    self._broadcast_drag_end(event)
                    self._drag_end()

                self._dump_shape_info("Master OnLeftUp - sending 'OnLeftUp' to", [shape])
                shape.OnLeftUp(event)

                # The INode 'drop' connection of shapes magic
                self._dump_shape_info(
                    "Master OnLeftUp - sending **'leftUp'**' to", [self.getSelectedShapes()]
                )
                shape.leftUp(self.getSelectedShapes())
            else:
                pass  # left up over emptiness
        except AttributeError as e:
            # forgive shapes not implementing leftUp, OnSizingEndDragLeft
            message = str(getattr(e, "message", repr(e)))
            if not ("leftUp" in message or "OnSizingEndDragLeft" in message):
                raise

        self._avoid_dangling_lines(resize_node or shape)
        self.commit_undo()

        self.Refresh()
        # print("after OnLeftUp, getSelectedShapes()=", self.getSelectedShapes())

    def _avoid_dangling_lines(self, leftup_shape):
        """If abort a drag line, then delete the ConnectionShape line.
        Can detect this situation when there is a single ConnectionShape in selected shapes, and
        the OnLeftUp happens over a ResizeableNode rather than an INode or ONode
        """
        if isinstance(leftup_shape, ResizeableNode) and len(self.getSelectedShapes()) == 1:
            shape = self.getSelectedShapes()[0]
            if isinstance(shape, ConnectionShape) and (shape.output is None or shape.input is None):
                self.diagram.DeleteShape(shape)
                self.deselect()  # delete associated Nodes that were attached to the ConnectionShape

    def _dragged_past_tolerance(self, event):
        """True once the pointer has moved far enough to start a drag.

        A click with a small hand tremor should not nudge a shape or resize it.
        Events without a position (scripted/fake events) always count as a drag.
        """
        get_position = getattr(event, "GetPosition", None)
        if get_position is None or self._drag_start_client is None:
            return True
        position = get_position()
        return (
            abs(position.x - self._drag_start_client.x) >= self.DRAG_TOLERANCE
            or abs(position.y - self._drag_start_client.y) >= self.DRAG_TOLERANCE
        )

    def OnMotion(self, event):
        """Calls move() on anything that is selected.  When resizing, a ResizeNode will be selected.
        When creating a connecting line, initially an ONode is selected (due to an initial OnLeftDown)
        then a newly spawned ConnectionLine is selected during the entire drag.
        """
        if self._marquee_active:
            self._marquee_update(event)
            return
        if getattr(self, "_panning", False):
            self._pan_move(event)
            return
        if not event.Dragging():
            if self._guides:
                self._guides = []
                self.Refresh()
            self._update_hover_ports(event)
            return
        # Corner resizes are proportional by default; Shift frees the aspect
        # ratio and Alt resizes from the shape's centre.  Resize nodes read
        # these while dragging.
        self._drag_free_aspect = bool(getattr(event, "ShiftDown", lambda: False)())
        self._drag_from_center = bool(getattr(event, "AltDown", lambda: False)())
        if not self._drag_started:
            if not self._dragged_past_tolerance(event):
                return
            self._drag_started = True
        point = self.getEventCoordinates(event)
        x = point[0] - self.currentPoint[0]
        y = point[1] - self.currentPoint[1]
        self._dump_canvas_info("OnMotion", point, x, y)

        move_shapes = [s for s in self.getSelectedShapes() if not isinstance(s, Node)]
        if move_shapes and self._drag_start_hull is not None:
            # Snap from the total offset since mouse-down, not the per-event
            # delta, so guides do not glue the shape in place.
            total_x = point[0] - self._drag_origin_diagram[0]
            total_y = point[1] - self._drag_origin_diagram[1]
            total_x, total_y = self._snap_drag(move_shapes, self._drag_start_hull, total_x, total_y)
            current_hull = self._hull(move_shapes)
            x = self._drag_start_hull[0] + total_x - current_hull[0]
            y = self._drag_start_hull[1] + total_y - current_hull[1]

        for shape in self.getSelectedShapes():
            shape.SetCanvas(self)  # safe-guard repair - ensure the shape knows its canvas
            self._dump_shape_info("OnMotion", [shape])

            shape.move(x, y)
            shape.MoveLinks(dc=None)

            self._record_drag(shape)

        self.currentPoint = point
        self.Refresh()

    def _record_drag(self, shape):
        # For possible later emission of an OnSizingEndDragLeft event
        if not isinstance(shape, (Node, ConnectionShape)):
            self._dragState = ContinueDraggingLeft
            self._draggedShape = shape

    def _drag_end(self):
        self._dragState = NoDragging
        self._draggedShape = None

    def _broadcast_drag_end(self, event):
        # A drag can end after the shape has already been deselected (for
        # example if a click arrives before the left-up).  Never assert in an
        # event handler: just forget the stale drag.
        if self._draggedShape not in self.getSelectedShapes():
            self._drag_end()
            return
        for _shape in self.getSelectedShapes():
            if DEBUG_DRAG:
                print("Master OnLeftUp - sending OnEndDragLeft to", self._draggedShape)
            # when sent to ConnectionShape, no OnEndDragLeft handler, thus caught in base shape event handler, pass
            # when sent to DividedShape, UmlShapeHandlerOglTwo class gets it and does important virtual canvas work etc.
            _shape.OnEndDragLeft(event)

    def GetDiagram(self):
        """Return the diagram associated with this canvas."""
        return self.diagram

    def SetDiagram(self, diagram):
        self.diagram = diagram
        if diagram is not None and getattr(diagram, "SetCanvas", None) is not None:
            diagram.SetCanvas(self)
        # Shapes may arrive from a loader (or be assigned directly) rather than
        # through this canvas, so make sure they all know their canvas.
        for shape in getattr(diagram, "shapes", []) or []:
            self._attach_canvas(shape)
        # A new diagram can have a different content origin (negative
        # coordinates); do not navigate last diagram's rectangle.
        self.invalidate_bounds_cache()

    def getCurrentShape(self, event):
        # get coordinate of click in our coordinate system
        point = self.getEventCoordinates(event)
        self.currentPoint = point
        # Look to see if an item is selected
        return self.shapeFromPoint(point)

    def shapeFromPoint(self, point):
        for item in self.nodes:
            if item._canvas is None:
                item.SetCanvas(self)
            if item.HitTest(point[0], point[1]):
                return item
        for item in reversed(self.diagram.shapes):
            if item.HitTest(point[0], point[1]):
                return item
        return None

    def getEventCoordinates(self, event):
        originX, originY = self.GetViewStart()
        unitX, unitY = self.GetScrollPixelsPerUnit()
        min_x, min_y = self._content_rect()[:2]
        return [
            (event.GetX() + (originX * unitX)) / self.scalex + min_x,
            (event.GetY() + (originY * unitY)) / self.scaley + min_y,
        ]

    # ----------------------------------------------------------------------
    # Zoom / pan / virtual size
    #
    # The canvas keeps a pair of zoom factors (``scalex`` and ``scaley``) and
    # applies them in ``onPaintEvent``.  Zoom is either anchored at the mouse
    # position (default), the selected shape, or the centre of the viewport.
    # The virtual size of the canvas tracks the bounds of all shapes plus a
    # small margin.  It never auto-shrinks (so zoom anchors don't get clamped);
    # maximise or zoom-to-fit will recompute it.
    # ----------------------------------------------------------------------

    def _scroll_offset_pixels(self):
        """Current scroll offset in pixels (GetViewStart is in scroll units)."""
        scroll_x, scroll_y = self.GetViewStart()
        unit_x, unit_y = self.GetScrollPixelsPerUnit()
        return scroll_x * unit_x, scroll_y * unit_y

    def mouse_pos_in_client_coords(self):
        """Mouse position in diagram coordinates (takes scroll and zoom into account)."""
        mouse_x, mouse_y = self.ScreenToClient(wx.GetMousePosition())
        return self.client_pos_in_diagram_coords(mouse_x, mouse_y)

    def client_pos_in_diagram_coords(self, x, y):
        scroll_x, scroll_y = self._scroll_offset_pixels()
        min_x, min_y = self._content_rect()[:2]
        return (x + scroll_x) / self.scalex + min_x, (y + scroll_y) / self.scaley + min_y

    def diagram_point_to_client_coords(self, x, y):
        scroll_x, scroll_y = self._scroll_offset_pixels()
        min_x, min_y = self._content_rect()[:2]
        return (x - min_x) * self.scalex - scroll_x, (y - min_y) * self.scaley - scroll_y

    def invalidate_bounds_cache(self):
        self._bounds_cache = None

    def getContentBounds(self):
        """Return ``(max_x, max_y)`` for the content the canvas should navigate.

        Subclasses can override this to exclude shapes that should not influence
        zoom-to-fit (for example, edges or decoration).  The default covers every
        top-level shape and its composite children.
        """
        max_x = max_y = 0

        def visit(shape):
            nonlocal max_x, max_y
            if shape.x and shape.y:
                max_x = max(max_x, max(shape.x))
                max_y = max(max_y, max(shape.y))
            for child in getattr(shape, "_compositeChildren", []) or []:
                visit(child)

        if self.diagram:
            for shape in getattr(self.diagram, "shapes", []):
                visit(shape)

        return max_x, max_y

    def getContentOrigin(self):
        """Return ``(min_x, min_y)`` for the content the canvas should navigate.

        This is the top-left corner of the scrollable area.  By default it
        covers every top-level shape and its composite children, so content can
        extend to negative diagram coordinates and still be reached by
        scrolling.  Subclasses overriding :meth:`getContentBounds` may override
        this too.
        """
        min_x = min_y = 0

        def visit(shape):
            nonlocal min_x, min_y
            if shape.x and shape.y:
                min_x = min(min_x, min(shape.x))
                min_y = min(min_y, min(shape.y))
            for child in getattr(shape, "_compositeChildren", []) or []:
                visit(child)

        if self.diagram:
            for shape in getattr(self.diagram, "shapes", []):
                visit(shape)

        return min_x, min_y

    def _content_rect(self):
        """Return cached ``(min_x, min_y, max_x, max_y)`` for all content."""
        if self._bounds_cache is None:
            min_x, min_y = self.getContentOrigin()
            max_x, max_y = self.getContentBounds()
            # Never let a stale/inconsistent override invert the rectangle.
            self._bounds_cache = (min(min_x, max_x), min(min_y, max_y), max_x, max_y)
        return self._bounds_cache

    def _shapes_bounds(self):
        """Return cached ``(max_x, max_y)`` content bounds."""
        return self._content_rect()[2:]

    def _zoom_anchor_point(self, anchor):
        # A concrete client point (e.g. the mouse wheel event position) wins.
        if isinstance(anchor, (tuple, list, wx.Point)):
            return self.client_pos_in_diagram_coords(anchor[0], anchor[1])
        if anchor == self.ZOOM_ANCHOR_SELECTION:
            selected = self.getSelectedShapes()
            if selected:
                shape = selected[0]
                return shape.GetX(), shape.GetY()
        if anchor == self.ZOOM_ANCHOR_CENTER:
            client_w, client_h = self.GetClientSize()
            return self.client_pos_in_diagram_coords(client_w / 2, client_h / 2)
        return self.mouse_pos_in_client_coords()

    def _apply_scrollbars(self, offset_x=0, offset_y=0):
        if self._in_resize:
            return
        self._in_resize = True
        try:
            min_x, min_y, max_x, max_y = self._content_rect()
            client_w, client_h = self.GetClientSize()
            unit_x, unit_y = self.GetScrollPixelsPerUnit()
            unit_x = unit_x or 1
            unit_y = unit_y or 1
            old_sx, old_sy = self._scroll_offset_pixels()

            # The virtual size covers the shapes plus a margin, and the scroll
            # position is clamped to it.  This is what stops zooming/panning
            # from wandering into an empty void (and "losing everything").
            # Content may extend into negative diagram coordinates, so measure
            # the extent rather than assuming the origin is (0, 0).
            content_w = int((max_x - min_x) * self.scalex) + self.CANVAS_MARGIN
            content_h = int((max_y - min_y) * self.scaley) + self.CANVAS_MARGIN
            want_w = max(client_w, content_w)
            want_h = max(client_h, content_h)
            max_sx = max(0, want_w - client_w)
            max_sy = max(0, want_h - client_h)
            new_sx = min(max(int(old_sx + offset_x), 0), max_sx)
            new_sy = min(max(int(old_sy + offset_y), 0), max_sy)

            # SetScrollbars works in scroll units, so convert the pixel sizes.
            self.SetScrollbars(
                unit_x,
                unit_y,
                int(want_w / unit_x),
                int(want_h / unit_y),
                int(new_sx / unit_x),
                int(new_sy / unit_y),
                noRefresh=True,
            )
        finally:
            self._in_resize = False

    def _zoom(self, amount=None, set_to_scale=None, reset=False, anchor=None):
        anchor = anchor or self.zoomAnchor
        old_scale = self.scalex
        if reset:
            new_scale = 1.0
        elif set_to_scale is not None:
            new_scale = set_to_scale
        else:
            new_scale = self.scalex + amount
        new_scale = max(self.ZOOM_MIN_SCALE, min(self.ZOOM_MAX_SCALE, new_scale))

        delta = new_scale - old_scale
        if abs(delta) < 1e-9:
            return

        anchor_x, anchor_y = self._zoom_anchor_point(anchor)
        self.scalex = self.scaley = new_scale

        # Keep the anchor under the same screen position while zooming.  Its
        # pixel position is measured from the content origin, not diagram (0,0).
        min_x, min_y = self._content_rect()[:2]
        offset_x = (anchor_x - min_x) * delta
        offset_y = (anchor_y - min_y) * delta
        self._apply_scrollbars(offset_x, offset_y)
        self.invalidate_bounds_cache()
        self.Refresh()

    def ZoomIn(self, step=None, anchor=None):
        """Zoom in (increase the scale by ``step``)."""
        self._zoom(step if step is not None else self.ZOOM_STEP, anchor=anchor)

    def ZoomOut(self, step=None, anchor=None):
        """Zoom out (decrease the scale by ``step``)."""
        self._zoom(-(step if step is not None else self.ZOOM_STEP), anchor=anchor)

    def ZoomTo(self, scale, anchor=None):
        """Zoom directly to ``scale`` (clamped to the min/max zoom range)."""
        self._zoom(set_to_scale=scale, anchor=anchor)

    def ZoomReset(self):
        """Zoom back to 100%."""
        self._zoom(reset=True, anchor=self.ZOOM_ANCHOR_CENTER)

    def ZoomToFit(self, margin=None):
        """Zoom so all shapes fit inside the viewport."""
        min_x, min_y, max_x, max_y = self._content_rect()
        bounds_x, bounds_y = max_x - min_x, max_y - min_y
        if bounds_x <= 0 or bounds_y <= 0:
            self.ZoomReset()
            return
        m = self.CANVAS_MARGIN if margin is None else margin
        client_w, client_h = self.GetClientSize()
        client_w = max(client_w - m, 1)
        client_h = max(client_h - m, 1)
        scale = min(client_w / bounds_x, client_h / bounds_y)
        self._zoom(set_to_scale=scale, anchor=self.ZOOM_ANCHOR_CENTER)
        # land at the origin so everything (which starts at (0, 0)) is on screen
        self.Scroll(0, 0)

    def CenterOn(self, diagram_x, diagram_y):
        """Scroll so the diagram position is centred in the viewport."""
        client_w, client_h = self.GetClientSize()
        unit_x, unit_y = self.GetScrollPixelsPerUnit()
        min_x, min_y = self._content_rect()[:2]
        target_x = int((diagram_x - min_x) * self.scalex - client_w / 2)
        target_y = int((diagram_y - min_y) * self.scaley - client_h / 2)
        self.Scroll(int(target_x / (unit_x or 1)), int(target_y / (unit_y or 1)))

    def update_virtual_size(self):
        """Recompute the virtual size from the bounds of all shapes."""
        self.invalidate_bounds_cache()
        self._apply_scrollbars()

    def OnMouseWheel(self, event):
        if not self.zoomInputEnabled:
            event.Skip()
            return

        delta = event.GetWheelDelta() or 120
        rotation = event.GetWheelRotation() / delta

        if event.ControlDown():
            # Anchor on the exact wheel position rather than the global mouse
            # position: they can differ, and the latter makes the zoom drift.
            position = event.GetPosition()
            if rotation > 0:
                self.ZoomIn(self.ZOOM_WHEEL_STEP, anchor=position)
            elif rotation < 0:
                self.ZoomOut(self.ZOOM_WHEEL_STEP, anchor=position)
            return

        # Plain wheel: scroll.  Accumulate fractional rotation so high-resolution
        # trackpad events move smoothly instead of being truncated to zero, and do
        # not multiply by GetLinesPerAction() - that made mac trackpads too fast.
        self._scroll_remainder += rotation * self.WHEEL_SCROLL_PIXELS
        amount = int(self._scroll_remainder)
        self._scroll_remainder -= amount
        sx, sy = self.GetViewStart()
        if (
            getattr(event, "GetWheelAxis", lambda: wx.MOUSE_WHEEL_VERTICAL)()
            == wx.MOUSE_WHEEL_VERTICAL
        ):
            self.Scroll(sx, sy - amount)
        else:
            self.Scroll(sx + amount, sy)

    def OnMagnify(self, event):
        """macOS trackpad pinch: zoom anchored at the pinch position."""
        if not self.zoomInputEnabled:
            event.Skip()
            return
        position = event.GetPosition()
        factor = 1.0 + event.GetMagnification()
        self._zoom(set_to_scale=self.scalex * factor, anchor=(position.x, position.y))

    def _pan_begin(self, event):
        self._panning = True
        self._pan_pending = True
        self._pan_start = event.GetPosition()
        self._pan_last = event.GetPosition()
        if not self.HasCapture():
            self.CaptureMouse()
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

    def _pan_end(self, event=None):
        if getattr(self, "_panning", False):
            self._panning = False
            self._pan_pending = False
            if self.HasCapture():
                self.ReleaseMouse()
            self.SetCursor(wx.NullCursor)

    def _pan_move(self, event):
        position = event.GetPosition()
        if getattr(self, "_pan_pending", False):
            # Ignore the first couple of pixels so a click with a tiny hand
            # tremor does not drag the canvas.
            if abs(position.x - self._pan_start.x) < self.PAN_START_THRESHOLD and (
                abs(position.y - self._pan_start.y) < self.PAN_START_THRESHOLD
            ):
                return
            self._pan_pending = False
            self._pan_last = position
            return
        delta = position - self._pan_last
        self._pan_last = position
        sx, sy = self.GetViewStart()
        self.Scroll(sx - delta.x, sy - delta.y)

    # end of zoom/pan section

    def getSelectedShapes(self):
        return self.selectedShapes

    def deselect(self, item=None):
        self._hover_shape = None
        if item is None:
            for s in self.selectedShapes:
                s.OnDeselect(None)
            del self.selectedShapes[:]
            del self.nodes[:]
        else:
            self.nodes = [n for n in self.nodes if n.item != item]
            self.selectedShapes = [n for n in self.selectedShapes if n != item]
            item.OnDeselect(None)

    def select(self, item=None):
        if item is None:
            return self.selectedShapes

        if isinstance(item, Node):
            del self.selectedShapes[:]
            self.selectedShapes.append(item)  # items here is a single node
            return

        if item not in self.selectedShapes:
            self.selectedShapes.append(item)
            item.OnSelect(None)
            # Note: no port nodes here.  Ports are drag handles, not selection
            # adornments: they appear when hovering a shape (see
            # _update_hover_ports) and as drop targets while a connection is
            # being dragged (see showInputs/showOutputs).  A finished edge is
            # an attached line routed via shape perimeters, never via ports.
            if isinstance(item, Resizeable):
                # Rectangles get eight handles (corners + edges); other
                # resizable shapes get one handle per x/y point.
                count = len(RECT_HANDLES) if _is_two_point_rect(item) else len(item.x)
                self.nodes.extend([ResizeableNode(item, n, self) for n in range(count)])
                self.verify_nodes_have_canvas()

    def showOutputs(self, item=None):
        if item:
            self.nodes.extend([ONode(item, n, self) for n in range(item.output)])
        elif item is None:
            for i in self.diagram.shapes:
                if isinstance(i, Connectable):
                    self.nodes.extend([ONode(i, n, self) for n in range(i.output)])
        self.verify_nodes_have_canvas()

    def showInputs(self, item=None):
        if isinstance(item, Block):
            self.nodes.extend([INode(item, n, self) for n in range(item.input)])
        else:
            for i in self.diagram.shapes:
                if isinstance(i, Connectable):
                    self.nodes.extend([INode(i, n, self) for n in range(i.input)])
        self.verify_nodes_have_canvas()

    def _show_hover_ports(self, shape):
        """Show the port nodes of one hovered shape (or clear them).

        Ports exist only as drag targets: hovering a connectable shape shows
        its ports so a connection can be started from them.
        """
        self._clear_hover_ports()
        if shape is None:
            return
        for n in range(shape.input):
            node = INode(shape, n, self)
            node._is_hover_port = True
            node.moveto(*shape.getPort("input", n))
            self.nodes.append(node)
        for n in range(shape.output):
            node = ONode(shape, n, self)
            node._is_hover_port = True
            node.moveto(*shape.getPort("output", n))
            self.nodes.append(node)
        self.verify_nodes_have_canvas()
        self._hover_shape = shape

    def _clear_hover_ports(self):
        """Remove any hover-shown port nodes."""
        self.nodes = [n for n in self.nodes if not getattr(n, "_is_hover_port", False)]
        self._hover_shape = None

    def _update_hover_ports(self, event):
        """Show ports on the shape under the mouse, if it is connectable."""
        if self.diagram is None:
            return
        point = self.getEventCoordinates(event)
        hovered = self.shapeFromPoint(point)
        if isinstance(hovered, Node):
            hovered = hovered.item
        if not isinstance(hovered, Connectable):
            hovered = None
        if hovered is not self._hover_shape:
            self._show_hover_ports(hovered)
            self.Refresh()

    def verify_nodes_have_canvas(self):
        for node in self.nodes:
            assert node.cf
            assert node._canvas

    def _dump_drag_info(self, msg, shape):
        if DEBUG_DRAG:
            print(
                f"{msg}: over shape: {shape} self._dragState={self._dragState} _draggedShape={self._draggedShape} getSelectedShapes()={self.getSelectedShapes()}"
            )

    def _dump_shape_info(self, msg, shapes: List[Shape]):
        if DEBUG_DRAG:
            indent = ""
            if len(shapes) > 1:
                print(f"{msg}: list of shapes being dumped: {shapes}")
                indent = "\t"
            for shape in shapes:
                if isinstance(shape, ConnectionShape):
                    print(
                        f"{indent}{msg}: ConnectionShape {shape} input {shape.input} output {shape.output}"
                    )
                else:
                    print(f"{indent}{msg}: shape: {shape}")

    def _dump_canvas_info(self, msg, point, x, y):
        if DEBUG_DRAG:
            print(
                "----\n%s: Dragging shapes %s mouse at %s canvas.currentPoint is %s thus moveto difference is (%s,%s)"
                % (msg, self.getSelectedShapes(), point, self.currentPoint, x, y)
            )
            print(f"canvas nodes: {self.nodes}")


# Abstract Classes ------------------------------------------------------------------------------------------
class Selectable:
    """
    Allows Shape to be selected
    """

    def __init__(self):
        # super().__init__()
        pass
        # self.dummy_test = 1

    # ANDY EXTRAS

    def Selected(self):
        """`True` if the shape is currently selected."""
        # return self._selected
        # return False
        if not self.GetCanvas():
            # print("hmm - no canvas on Selectable?", self)
            return []
        return self in self.GetCanvas().getSelectedShapes()  # Andy idea

    def Select(self, select, dc=None):
        """
        Select or deselect the given shape, drawing or erasing control points
        (handles) as necessary.

        :param `select`: `True` to select
        :param `dc`: the device context

        """
        # self._selected = select
        # if select:
        #     self.MakeControlPoints()
        #     # Children of divisions are contained objects,
        #     # so stop here
        #     if not isinstance(self, DivisionShape):
        #         for child in self._children:
        #             child.MakeMandatoryControlPoints()
        #     if dc:
        #         self.GetEventHandler().OnDrawControlPoints(dc)
        # else:
        #     self.DeleteControlPoints(dc)
        #     if not isinstance(self, DivisionShape):
        #         for child in self._children:
        #             child.DeleteControlPoints(dc)

        self.GetCanvas().select(self)  # ANDY - ogllike version :-)


class Resizeable:
    """
    Creates resize Nodes that can be drug around the canvas
    to alter the shape or size of the Shape
    """

    def __init__(self):
        pass


class Connectable:
    """
    Creates connection nodes or ports
    New version only has one port for in and one for out - at centre of shape's side
    And for drawing, the ConnectionShape asks the Shape for its centre via this class
        (Blocks etc. inherit from this class, thus have the getCentre() method available)
        Note, ConnectionShape does not inherit from this class.
    """

    def __init__(self):
        self.input = 1
        self.output = 1
        self.connections = []  # this will be the list containing downstream connections

    # def getPortXX(self, type, num):
    #     if type == "input":
    #         x = self.x[0]
    #     elif type == "output":
    #         x = self.x[1]
    #     y = self.y[0]
    #     return (x, y)
    #
    # def getPortXXXX(self, type, num):
    #     # calc centre - the problem is that input node and output node on the same point
    #     # and cannot be distinguished, meaning often try to drag from an input node, which
    #     # is 'undefined' and buggy.
    #     x = self.x[0] + (self.x[1] - self.x[0]) / 2
    #     y = self.y[0] + (self.y[1] - self.y[0]) / 2
    #     return (x, y)
    #
    # def getPortZ(self, type, num):
    #     # calc almost centre
    #     x = self.x[0] + (self.x[1] - self.x[0]) / 2
    #     y = self.y[0] + (self.y[1] - self.y[0]) / 2
    #     if type == "input":
    #         x -= 10
    #     return (x, y)

    def getPort(self, type, num):
        """Return a port position as ``(x, y)``.

        Port 0 (the default) is the centre of the left side for inputs and the
        right side for outputs.  Ports 1 and 2 are the centres of the top and
        bottom edges, so vertical relationships can be connected to real ports
        and follow the shape when it moves.
        """
        if num == 1:  # top centre
            return ((self.x[0] + self.x[1]) / 2.0, self.y[0])
        if num == 2:  # bottom centre
            return ((self.x[0] + self.x[1]) / 2.0, self.y[1])
        # centre of left and right sides
        if type == "input":
            x = self.x[0]
        elif type == "output":
            x = self.x[1]
        y = self.y[0] + (self.y[1] - self.y[0]) / 2
        return (x, y)

    def getCentre(self):
        # calc centre
        x = self.x[0] + (self.x[1] - self.x[0]) / 2
        y = self.y[0] + (self.y[1] - self.y[0]) / 2
        return (x, y)


class Attributable:
    """
    Allows AttributeEditor to edit specified properties
    of the Shape
    """

    def __init__(self):
        self.attributes = []

    def AddAttribute(self, name):
        self.attributes.append(name)

    def AddAttributes(self, atts):
        self.attributes.extend(atts)

    def RemoveAttribute(self, name):
        self.attributes.remove(name)


# ------------------------------------------------------------------------------------------------------------


class LinesShape(Shape, Resizeable):
    def __init__(self, points):
        Shape.__init__(self)
        self.x = []
        self.y = []
        for p in points:
            self.x.append(p[0])
            self.y.append(p[1])

    def draw(self, dc):
        Shape.draw(self, dc)
        ind = 0
        try:
            while 1:
                dc.DrawLine(
                    int(self.x[ind]), int(self.y[ind]), int(self.x[ind + 1]), int(self.y[ind + 1])
                )
                ind = ind + 1
        except IndexError:
            pass

    def HitTest(self, x, y):

        if x < min(self.x) - 3:
            return False
        if x > max(self.x) + 3:
            return False
        if y < min(self.y) - 3:
            return False
        if y > max(self.y) + 3:
            return False

        ind = 0
        try:
            while 1:
                x1 = self.x[ind]
                y1 = self.y[ind]
                x2 = self.x[ind + 1]
                y2 = self.y[ind + 1]

                top = (x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)
                distsqr = pow(x1 - x2, 2) + pow(y1 - y2, 2)
                u = float(top) / float(distsqr)

                newx = x1 + u * (x2 - x1)
                newy = y1 + u * (y2 - y1)

                dist = pow(pow(newx - x, 2) + pow(newy - y, 2), 0.5)

                if dist < 7:
                    return True
                ind = ind + 1
        except IndexError:
            pass
        return False


class ConnectionShape(LineShapeBase, Resizeable, Selectable):
    def __init__(self):
        LineShapeBase.__init__(self)
        Resizeable.__init__(self)
        self.input = None
        self.output = None

    def setInput(self, shape, portnum):
        """
        Set the object and port you are dragging/connecting from
        Assign to self.input which is a tuple comprising (shape, portnum) where the portnum
        is a rhs output portnum, since we draw from an output port to an input port.

        Args:
            shape: the shape you are dragging from
            portnum: the port number 0..n you are dragging from

        Returns: -

        """
        self.input = (shape, portnum)

    def setOutput(self, shape, portnum):
        self.output = (shape, portnum)

    def draw(self, dc):
        # SHAPE = 0
        # PORT = 1
        discrepancy_x = 0
        discrepancy_y = 0
        currentMousePoint = self._canvas.currentPoint if self._canvas else (9999, 9999)

        if self.input:
            # self.x[0],self.y[0] = self.input[SHAPE].getPort('output',self.input[PORT])  # Original code

            shape, portnum = self.input
            # Always draw from the port.  Using the centre while unselected and
            # the port while selected made a connection visibly jump the moment
            # it was clicked.
            point = shape.getPort("output", portnum)
            self.x[0], self.y[0] = point

            # Fix any discrepancy re current TO drag position
            if self._canvas:
                discrepancy_x = self.x[1] - self._canvas.currentPoint[0]
                discrepancy_y = self.y[1] - self._canvas.currentPoint[1]

            if DEBUG_CONNECT:
                print("from shape output port %s at %s" % (portnum, point), end=" ")
                if not self.output:
                    print(
                        " to NOTHING, self.x[1], self.y[1] are",
                        self.x[1],
                        self.y[1],
                        "mouse at",
                        currentMousePoint,
                        "DISCREPANCY",
                        discrepancy_x,
                        discrepancy_y,
                    )

            # NOTE: the free end is tracked by OnMotion calling move() on this
            # line.  Do *not* snap it to canvas.currentPoint here: draw() runs
            # on every repaint, and currentPoint is updated by unrelated
            # clicks, which used to drag the edge routing to wherever the user
            # last clicked.

        if self.output:
            # self.x[1],self.y[1] = self.output[SHAPE].getPort('input',self.output[PORT])

            shape, portnum = self.output
            point = shape.getPort("input", portnum)
            self.x[1], self.y[1] = point

            # Fix any discrepancy re current TO drag position
            if (
                self._canvas and self.input is None
            ):  # doing a backwards drag from an input port (lhs of a shape)
                discrepancy_x = self.x[0] - self._canvas.currentPoint[0]
                discrepancy_y = self.y[0] - self._canvas.currentPoint[1]

            if DEBUG_CONNECT:
                if self.input is None:
                    print(
                        "FROM shape input port %s at %s" % (portnum, point),
                        "which is a BACKWARDS connection",
                        "mouse at",
                        currentMousePoint,
                        "DISCREPANCY",
                        discrepancy_x,
                        discrepancy_y,
                    )
                else:
                    print(
                        "to shape input port %s at %s" % (portnum, point), "self.input=", self.input
                    )

            # NOTE: see above - the free end follows move(), not currentPoint.

        LineShapeBase.draw(self, dc)

    # ANDY EXTRAS

    def GetParent(self):
        """Get the parent of this shape, if it is part of a composite."""
        # return self._parent
        return None


class TextShape(Shape):
    """A non-interactive text label.

    Useful for section headings and annotations.  It is not hit-testable, so it
    never gets in the way of selecting the shapes around it.
    """

    marqueeSelectable = False

    def __init__(self, x=0, y=0, text="", colour="GRAY", font=None):
        Shape.__init__(self, [x], [y])
        self.label = text
        self._font = font
        self.SetLabelColour(colour)

    def SetLabelColour(self, colour):
        if isinstance(colour, str):
            colour = wx.TheColourDatabase.Find(colour)
        self.label_colour = colour

    def draw(self, dc):
        font = self._font or wx.Font(
            10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        dc.SetFont(font)
        dc.SetTextForeground(self.label_colour)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.DrawText(self.label, int(self.x[0]), int(self.y[0]))

    def HitTest(self, x, y):
        return False

    def move(self, x, y):
        self.x[0] += x
        self.y[0] += y


class SelectableTextShape(TextShape, Selectable):
    """A text caption that can be selected and moved (no resize handles)."""

    marqueeSelectable = True

    def __init__(self, x=0, y=0, text="", colour="GRAY", font=None):
        TextShape.__init__(self, x, y, text, colour, font)
        Selectable.__init__(self)
        self._measure()

    def _font_for_measure(self):
        return self._font or wx.Font(
            10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )

    def _measure(self):
        bitmap = wx.Bitmap(1, 1)
        dc = wx.MemoryDC(bitmap)
        try:
            dc.SetFont(self._font_for_measure())
            width, height = dc.GetTextExtent(self.label)
        finally:
            dc.SelectObject(wx.NullBitmap)
        self._text_width = width
        self._text_height = height

    def SetLabel(self, text):
        self.label = text
        self._measure()

    def GetBoundingBoxMin(self):
        return getattr(self, "_text_width", 0), getattr(self, "_text_height", 0)

    def HitTest(self, x, y):
        width, height = self.GetBoundingBoxMin()
        left, top = self.x[0], self.y[0]
        return left <= x <= left + width and top <= y <= top + height

    def draw(self, dc):
        TextShape.draw(self, dc)
        # Keep the measured bounds in sync if the font/label changed directly.
        if (
            getattr(self, "_text_width", None) is None
            or getattr(self, "_text_height", None) is None
        ):
            self._measure()


class ResizableRectangleShape(RectangleShape, Selectable, Resizeable):
    """A plain rectangle that can be selected and resized."""

    def __init__(self, x=20, y=20, x2=140, y2=100):
        RectangleShape.__init__(self, x, y, x2, y2)
        Resizeable.__init__(self)
        Selectable.__init__(self)


class Block(RectangleShape, Connectable, Resizeable, Selectable, Attributable):
    def __init__(self):
        x, y, x2, y2 = 20, 20, 90, 90
        RectangleShape.__init__(self, x, y, x2, y2)
        Resizeable.__init__(self)
        Connectable.__init__(self)
        Attributable.__init__(self)
        self.AddAttributes(["label", "pen", "fill", "input", "output"])
        self.label = "Block"
        # Text colour must be set explicitly: a PaintDC may start with a
        # disabled/white foreground, and the colour left behind by the
        # previously drawn shape is not ours to rely on.
        self.label_colour = wx.BLACK

    def SetLabelColour(self, colour):
        """Set the label colour (a colour name or a wx.Colour)."""
        if isinstance(colour, str):
            colour = wx.TheColourDatabase.Find(colour)
        self.label_colour = colour

    def draw(self, dc):
        RectangleShape.draw(self, dc)
        dc.SetFont(self._font)  # ANDY ADDED - otherwise other font changes by other shapes...
        dc.SetTextForeground(self.label_colour)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        w, h = dc.GetTextExtent(self.label)
        mx = int((self.x[0] + self.x[1]) / 2.0) - int(w / 2.0)
        my = int((self.y[0] + self.y[1]) / 2.0) - int(h / 2.0)
        dc.DrawText(self.label, mx, my)

    def OnLeftDown(self, event):
        if isinstance(self, Block) and event.ControlDown():
            d = wx.TextEntryDialog(None, "Block Label", defaultValue=self.label, style=wx.OK)
            d.ShowModal()
            self.label = d.GetValue()

    def OnRightDown(self, event):
        # Kept as a no-op: right-click menus are owned by the application
        # (see the demo's context menu and pynsource's shape menu).
        pass

    """
    Attempt to have a r.click menu on the shape, but this needs to be done in the shapecanvas window
    not in the individual shape because only the shape window has access to the .diagram object 
    which allows shape deletion.  Shapes don't have a back pointer to the shapecanvas window or to 
    the diagram which houses it, unfortunately.  
        - We need the shapecanvas window in order to bind popup menu etc. events
        - We need the shapecanvas window .diagram to access delete shape method 
    ANDYMAIN was a failed attempt to record the last shapecanvas window, which was hacky, and 
    also failed since there are nested containers in this demo.
    """
    # ANDY
    # def OnRightDown(self,event):
    #     self.popupmenu = Menu()
    #     item = self.popupmenu.Append(2011, "Properties...")
    #     ANDYMAIN.canvas.Bind(EVT_MENU, self.OnPopupItemSelected, item)
    #     item = self.popupmenu.Append(2012, "Delete Node")
    #     ANDYMAIN.canvas.Bind(EVT_MENU, self.OnPopupItemSelected, item)
    #     item = self.popupmenu.Append(2013, "Cancel")
    #     ANDYMAIN.canvas.Bind(EVT_MENU, self.OnPopupItemSelected, item)
    #     #
    #     pos = event.GetPosition()
    #     # pos = ANDYMAIN.canvas.ScreenToClient(pos)
    #     ANDYMAIN.canvas.PopupMenu(self.popupmenu, pos)
    # ##########
    #
    # #ANDY
    # def OnPopupItemSelected(self, event):
    #     item = self.popupmenu.FindItemById(event.GetId())
    #     text = item.GetText()
    #     #wx.MessageBox("You selected item '%s'" % text)
    #     if text == "Properties...":
    #         f = AttributeEditor(None, -1, "props",self)
    #         # f.moveto(item.x, item.y)  # ANDY
    #         f.Show(True)
    #     elif text == "Delete Node":
    #         print "Delete Node"
    #         # Block is a shape, but we need to get to the diagram which this shape is part of
    #         # we cannot, so move this logic into the ShapeCanvas not the Shape
    #         # self.diagram.DeleteShape(s)
    #         # self.deselect() #remove nodes

    def AddText(self, string):
        """Add a line of text to the shape's default text region."""
        # if not self._regions:
        #     return
        #
        # region = self._regions[0]
        # #region.ClearText()
        # new_line = ShapeTextLine(0, 0, string)
        # text = region.GetFormattedText()
        # text.append(new_line)
        #
        # self._formatted = False

        self.label = string


################ New Shapes


class EllipseShape(Shape):
    def __init__(self, x=20, y=20, x2=90, y2=90):
        Shape.__init__(self, [x, x2], [y, y2])
        self._width = x2 - x
        self._height = y2 - y

    def GetWidth(self):
        return self.x[1] - self.x[0]

    def GetHeight(self):
        return self.y[1] - self.y[0]

    def draw(self, dc):
        """The draw handler."""
        # if self._shadowMode != SHADOW_NONE:
        #     if self._shadowBrush:
        #         dc.SetBrush(self._shadowBrush)
        #     dc.SetPen(TransparentPen)
        #     dc.DrawEllipse(self._xpos - self.GetWidth() / 2.0 + self._shadowOffsetX,
        #                    self._ypos - self.GetHeight() / 2.0 + self._shadowOffsetY,
        #                    self.GetWidth(), self.GetHeight())

        # if self._pen:
        #     if self._pen.GetWidth() == 0:
        #         dc.SetPen(TransparentPen)
        #     else:
        #         dc.SetPen(self._pen)

        # if self._brush:
        #     dc.SetBrush(self._brush)

        # Drawn so it fits inside rectangle.  wx DCs require ints (Python 3.10+
        # no longer silently truncates floats), and dragging a shape adds float
        # deltas to x/y, so cast here.
        dc.DrawEllipse(int(self.x[0]), int(self.y[0]), int(self.GetWidth()), int(self.GetHeight()))

    def HitTest(self, x, y):
        # Crude copy of Rectangle test
        if x < self.x[0]:
            return False
        if x > self.x[1]:
            return False
        if y < self.y[0]:
            return False
        if y > self.y[1]:
            return False
        return True


class ConnectableEllipseShape(EllipseShape, Connectable, Resizeable, Selectable, Attributable):
    def __init__(self):
        x, y, x2, y2 = 20, 20, 90, 90
        EllipseShape.__init__(self, x, y, x2, y2)
        Resizeable.__init__(self)
        Connectable.__init__(self)
        Attributable.__init__(self)
        # self.AddAttributes(['label', 'pen', 'fill', 'input', 'output'])
        # self.label = 'Block'

    ################


# Nodes
class Node(PointShape):
    def __init__(self, item, index, cf):
        # print "Node creation item=%s index=%s cf=%s" % (item,index,cf)
        self.item = item  # shape to which node is attached
        self.index = index  # portnum
        self.cf = cf  # shape canvas  # TODO two canvas attrs, consolidate into one
        # print("Node", self, "created, self._canvas=", self._canvas)
        PointShape.__init__(self)
        # Set _canvas AFTER the PointShape/Shape init, cos they set _canvas to None
        self._canvas = cf  # shape canvas  # TODO two canvas attrs, consolidate into one
        assert self.cf
        assert self._canvas

    def showProperties(self):
        self.item.showProperties


class ConnectableNode(Node):
    def __init__(self, item, index, cf):
        Node.__init__(self, item, index, cf)
        assert self.cf
        assert self._canvas
        self.edge_type = "association"

    def recreate_line_properly(self, connection_shape):
        """Delete the connection shape and call canvas.join_shapes() which gives an opportunity
        for subclasses of canvas to create custom lines e.g. umlcanvas creates fancy uml lines."""
        if DEBUG_DRAG:
            print(
                f"INode.leftup(): NEED TO BROADCAST - please connect {connection_shape.input} to {connection_shape.output}, {self.edge_type} to canvas={self._canvas}"
            )
        if self._canvas:
            fromShape = connection_shape.input[0]
            toShape = connection_shape.output[0]
            self._canvas.DeleteShape(connection_shape)
            self._canvas.deselect()  # remove nodes

            self._canvas.join_shapes(fromShape, toShape, self.edge_type)  # <<-- magic broadcast
        else:
            # Critical tht we have the shape INode pointing back to the canvas
            if DEBUG_DRAG:
                print("INode.leftup()", self, "self._canvas is NONE - CANNOT BROADCAST!!")

    def OnLeftUp(self, event):
        """This event gets called before the leftUp() event, so record the state of the keys"""
        # print(f"event shiftDown={event.shiftDown} controlDown={event.controlDown} altDown={event.altDown}")
        if event.shiftDown:
            self.edge_type = "generalisation"
        elif event.altDown:
            self.edge_type = "composition"


class INode(ConnectableNode):
    def __init__(self, item, index, cf):
        ConnectableNode.__init__(self, item, index, cf)

    def leftUp(self, connection_shapes):
        """
        This gets called when you release the mouse when connecting to a destination input port
        The ConnectionShape item has .input and .output containing (shape, portnum) each.

        To know the 'from' shape you look at the ConnectionShape.input[0] which has an output node on a portnum
         and to know the 'to' shape you look at the ConnectionShape.output[0] which has an input node

        Args:
            connection_shapes: list of ConnectionShape instances (really, only one)
        """
        if DEBUG_INODE_CONNECT:
            print(
                "INode.leftup(connection_shapes) where connection_shapes=",
                connection_shapes,
                "ConnectionShape.input",
                connection_shapes[0].input,
                "ConnectionShape.output",
                connection_shapes[0].output,
            )
        if len(connection_shapes) == 1 and isinstance(connection_shapes[0], ConnectionShape):
            connection_shape = connection_shapes[0]
            if connection_shape.output is None:  # means its not connected to anything
                connection_shape.setOutput(self.item, self.index)
                self.recreate_line_properly(connection_shape)

    def move(self, x, y):
        """
        Dragging from an input to an output - backwards :-)
        """
        self.cf.deselect()
        ci = ConnectionShape()
        self.cf.diagram.shapes.insert(0, ci)
        ci.setOutput(self.item, self.index)
        ci.x[0], ci.y[0] = self.item.getPort("input", self.index)
        self.cf.showOutputs()
        self.cf.select(ci)

    def draw(self, dc):
        """Draws a white square input connector node on the left edge of a shape"""
        # Each node instance has a property index (portnum) baked into it, as well as the item (shape)
        # Draw yourself on the shape at coords of the portnum on the input side (cos this is an INode)
        x, y = self.item.getPort("input", self.index)
        self.moveto(x, y)
        PointShape.draw(self, dc)


class ONode(ConnectableNode):
    def __init__(self, item, index, cf):
        ConnectableNode.__init__(self, item, index, cf)

    def move(self, x, y):
        """
        initiating a connection from output node, creating the shape and adding it to the
        shapecanvas, setting the input, output to be set later when leftUp over INode

        Note the subsequent multiple move() calls due to the OnMotion() goes to the
        ConnectionShape not to the ONode.
        """
        # print("ONode initiating a connection from output node", self)
        self.cf.deselect()
        ci = ConnectionShape()
        self.cf.diagram.shapes.insert(0, ci)
        ci.setInput(self.item, self.index)
        ci.x[1], ci.y[1] = self.item.getPort("output", self.index)
        self.cf.showInputs()
        self.cf.select(ci)

    def leftUp(self, connection_shapes):
        # Not sure the use of this, I don't think the setInput() ever gets executed
        # print("onode leftup", items)
        if len(connection_shapes) == 1 and isinstance(connection_shapes[0], ConnectionShape):
            connection_shape = connection_shapes[0]
            if connection_shape.input is None:
                # print("onode leftup, setting input", items)
                connection_shape.setInput(self.item, self.index)
                self.recreate_line_properly(connection_shape)

    def draw(self, dc):
        x, y = self.item.getPort("output", self.index)
        self.moveto(x, y)
        PointShape.draw(self, dc)


def _is_two_point_rect(shape):
    """True if ``shape`` is rectangle-like with exactly two x/y points."""
    return isinstance(shape, RectangleShape) and len(shape.x) == 2 and len(shape.y) == 2


#: Handle layout for a two-point rectangle: ``(x_index, y_index)`` per handle.
#: ``None`` on an axis means an edge handle that only drags the other axis.
#: Indices 0 and 1 are the historical corners (top-left, bottom-right).
RECT_HANDLES = (
    (0, 0),  # 0 top-left
    (1, 1),  # 1 bottom-right
    (1, 0),  # 2 top-right
    (0, 1),  # 3 bottom-left
    (0, None),  # 4 left
    (1, None),  # 5 right
    (None, 0),  # 6 top
    (None, 1),  # 7 bottom
)


def resize_rect_from_handle(shape, index, dx, dy, free_aspect=False, from_center=False):
    """Resize a two-point rectangle by dragging the handle at ``index``.

    ``index`` selects a corner or an edge from :data:`RECT_HANDLES`.  The
    opposite corner/edge stays fixed, the size is clamped to one unit instead
    of inverting, and corner drags are proportional unless ``free_aspect`` is
    set (driven by whichever axis moved further).  Edge drags change one axis
    only.  ``from_center`` grows/shrinks both sides symmetrically instead of
    anchoring the opposite corner.  Used by ``ResizeableNode`` for rectangle
    shapes and by ``ResizableBitmapShape.move_handle``.
    """
    if len(shape.x) != 2 or len(shape.y) != 2:
        shape.x[index] += dx
        shape.y[index] += dy
        return

    xi, yi = RECT_HANDLES[index] if 0 <= index < len(RECT_HANDLES) else (1, 1)
    old_width = abs(shape.x[1] - shape.x[0])
    old_height = abs(shape.y[1] - shape.y[0])
    center_x = (shape.x[0] + shape.x[1]) / 2.0
    center_y = (shape.y[0] + shape.y[1]) / 2.0
    width = old_width
    height = old_height

    # Resizing from the centre moves both sides, so the same mouse delta
    # changes the size twice as much.
    factor = 2.0 if from_center else 1.0

    if xi is not None:
        sign = 1.0 if xi == 1 else -1.0
        width = max(1.0, old_width + sign * dx * factor)
    if yi is not None:
        sign = 1.0 if yi == 1 else -1.0
        height = max(1.0, old_height + sign * dy * factor)

    if not free_aspect and xi is not None and yi is not None and old_width > 0 and old_height > 0:
        ratio = old_width / old_height
        if abs(width - old_width) >= abs(height - old_height):
            height = max(1.0, width / ratio)
        else:
            width = max(1.0, height * ratio)

    if xi is not None:
        if from_center:
            shape.x[0] = center_x - width / 2.0
            shape.x[1] = center_x + width / 2.0
        else:
            shape.x[0 if xi == 0 else 1] = shape.x[1] - width if xi == 0 else shape.x[0] + width
    if yi is not None:
        if from_center:
            shape.y[0] = center_y - height / 2.0
            shape.y[1] = center_y + height / 2.0
        else:
            shape.y[0 if yi == 0 else 1] = shape.y[1] - height if yi == 0 else shape.y[0] + height


class ResizeableNode(Node):
    """A resize grab handle for a shape.

    Rectangle-like shapes get eight handles (four corners and four edges, see
    :data:`RECT_HANDLES`); other resizable shapes get one per x/y point (lines,
    polygons).
    """

    def __init__(self, item, index, cf):
        Node.__init__(self, item, index, cf)
        self.fill = ["BLACK"]
        self.handle = self._handle_descriptor(index)
        # Position the handle straight away: hit-testing uses the graphic and
        # draw() is the only other place that positions it.  Without this a
        # handle cannot be grabbed between select() and the next paint, so a
        # click near a corner drags the shape instead of resizing it.
        point = self._handle_xy()
        if point is not None:
            self.moveto(*point)

    def _handle_descriptor(self, index):
        item = self.item
        if _is_two_point_rect(item) and 0 <= index < len(RECT_HANDLES):
            return RECT_HANDLES[index]
        return (index, index)

    def _handle_xy(self):
        """Current position of this handle in diagram coordinates."""
        item = self.item
        xi, yi = self.handle
        if xi is None:
            if len(item.x) < 2:
                return None
            x = (item.x[0] + item.x[1]) / 2.0
        elif xi < len(item.x):
            x = item.x[xi]
        else:
            return None
        if yi is None:
            if len(item.y) < 2:
                return None
            y = (item.y[0] + item.y[1]) / 2.0
        elif yi < len(item.y):
            y = item.y[yi]
        else:
            return None
        return x, y

    def draw(self, dc):
        point = self._handle_xy()
        if point is not None:
            self.moveto(*point)
        PointShape.draw(self, dc)

    def move(self, x, y):
        """Resize" scenario - Resize the shape! - Changes the coords of the specific point on the shape
        that this ResizeableNode is attached to (viz. self.item) which can be a regular shape or
        even a ConnectionShape. Point is ONE (the port) of a pair of points typically on the
        rect shape's corner either left, top or right,bottom - or a center point of the rect shape.
        In the case of a LineShape, points are on either end (still a pair of
        xy points l,t -> r,b except we draw a line rather than a square).

        Called via canvas.OnMotion since in this scenario, a ResizeableNode is the object in
        canvas.getSelectedShapes (OnMotion calls .move on all things in canvas.getSelectedShapes()).
        Remember though that ConnectionShape self corrects its own xy points during the draw,
        which means you can never "resize" a ConnectionShape line.

        However a different kind of line shape e.g. UML line, may not self correct its own
        xy points.
        Also the call to MoveLinks() might cause issues.

        Changes coords of the point on ResizeableNode's shape's corner by delta x, y.
        The self.index selects which point/edge of the shape this node drags
        (for a rectangle: see RECT_HANDLES), and self.item is the shape.
        """
        # print("ResizeableNode move() self.index", self.index)
        item = self.item
        # Proportional by default: Shift frees the aspect ratio.  OnMotion
        # records the modifier for us.
        free_aspect = bool(getattr(self.cf, "_drag_free_aspect", False))
        from_center = bool(getattr(self.cf, "_drag_from_center", False))
        move_handle = getattr(item, "move_handle", None)
        if move_handle is not None:
            if move_handle(self.index, x, y, free_aspect=free_aspect, from_center=from_center):
                # LineShape keeps its geometry in control points; it has already
                # updated x/y from them, so do not move x/y again.
                item.MoveLinks(dc=None)
                self._sync_to_item()
                return
        elif _is_two_point_rect(item):
            # Corner drag: keep the opposite corner fixed and never invert the
            # rectangle, which used to trip RectangleShape.sanity() on hit-test.
            resize_rect_from_handle(item, self.index, x, y, free_aspect, from_center)
            item.MoveLinks(dc=None)
            self._sync_to_item()
            return
        item.x[self.index] += x
        item.y[self.index] += y
        item.MoveLinks(dc=None)
        self._sync_to_item()

    def _sync_to_item(self):
        """Keep the handle under the mouse while dragging (hit-testing uses graphic)."""
        point = self._handle_xy()
        if point is not None:
            self.moveto(*point)

    def leftUp(self, selected_ResizableNodes):  # ANDY ADDED
        """when resize finishes, simulate wx.ogl event of same name"""
        resizable_node = self

        if resizable_node not in selected_ResizableNodes:
            # The selection can legitimately change before mouse-up; not an error.
            pass

        shape = self.item  # actual shape being re-sized
        point = self._handle_xy() or (shape.GetX(), shape.GetY())

        # Clear the ResizableNode out of being selected, and select the shape being re-sized
        self.cf.deselect()
        self.cf.select(shape)

        shape.OnSizingEndDragLeft(pt=None, x=point[0], y=point[1], keys=None, attch=None)


# ---------------------------------------------------------------------------------------------------------


# Util - ANDY


################################
