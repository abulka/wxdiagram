import sys
import math

import wx
from .core import RectangleShape, Resizeable, Selectable, Shape
from .geometry import (
    ARROW_ARROW,
    ARROW_FILLED_CIRCLE,
    ARROW_HOLLOW_CIRCLE,
    ARROW_METAFILE,
    ARROW_POSITION_END,
    ARROW_POSITION_MIDDLE,
    ARROW_POSITION_START,
    ARROW_SINGLE_OBLIQUE,
    ATTACHMENT_MODE_NONE,
    GetArrowPoints,
    GetPointOnLine,
    GraphicsStraightenLine,
    line_control_points_to_xy_points,
)
from .basic import get_black_foreground_pen
from .core import LineShapeBase
from .basic import ShapeRegion, ShapeTextLine
from . import routing

# local OGL LineShape doesn't have much, so add....
# actually a lot of stuff has been added to core module LineShapeOri


class LineShape(LineShapeBase, Selectable, Resizeable):
    #: Route attached lines around unrelated rectangles.  ``False`` (default)
    #: keeps the exact straight-line look; ``True`` avoids obstacles only;
    #: ``"curved"`` draws a free bezier even when the path is clear (the usual
    #: UML look), still escalating to a bigger bend or an orthogonal lane when
    #: boxes are in the way.
    autoRoute = False

    def __init__(self):
        LineShapeBase.__init__(self)
        # Selectable.__init__(self)  # no need

        self._isSpline = False
        self._attachmentTo = 0
        self._attachmentFrom = 0
        self._from = None
        self._to = None
        # self._sensitivity = OP_CLICK_LEFT | OP_CLICK_RIGHT
        # self._draggable = False
        self._erasing = False
        # self._arrowSpacing = 5.0
        self._ignoreArrowOffsets = False
        # self._maintainStraightLines = False
        # self._alignmentStart = 0
        # self._alignmentEnd = 0
        self._lineControlPoints = None

        # Clear any existing regions (created in an earlier constructor)
        # and make the three line regions.
        self.ClearRegions()
        for name in ["Middle", "Start", "End"]:
            newRegion = ShapeRegion()
            newRegion.SetName(name)
            newRegion.SetSize(150, 50)
            self._regions.append(newRegion)

        self._labelObjects = [None, None, None]
        self._lineOrientations = []
        self._lineControlPoints = []
        self._arcArrows = []
        #: on-screen label rectangles, filled in by DrawLabels for hit-testing
        self._labelRects = {}

    def DrawArrow(self, dc, arrow, XOffset, proportionalOffset):
        """
        Draw the given arrowhead (or annotation).

        :param `dc`: a :class:`wx.PaintDC`/:class:`wx.MemoryDC`
        :param `arrow`: an :class:`ArrowHead`
        :param `XOffset`: the offset from the end of the line, or a proportion of
          the line length (in 0..1) when `proportionalOffset` is True
        :param `proportionalOffset`: `True` when `XOffset` is a proportion of the line length
        """
        first_line_point = self._lineControlPoints[0]
        second_line_point = self._lineControlPoints[1]

        last_line_point = self._lineControlPoints[-1]
        second_last_line_point = self._lineControlPoints[-2]

        # Position of start point of line, at the end of which we draw the arrow
        startPositionX, startPositionY = 0.0, 0.0

        ap = arrow.GetPosition()
        if ap == ARROW_POSITION_START:
            # If we're using a proportional offset, calculate just where this
            # will be on the line.
            realOffset = XOffset
            if proportionalOffset:
                totalLength = math.sqrt(
                    (second_line_point[0] - first_line_point[0])
                    * (second_line_point[0] - first_line_point[0])
                    + (second_line_point[1] - first_line_point[1])
                    * (second_line_point[1] - first_line_point[1])
                )
                realOffset = XOffset * totalLength

            positionOnLineX, positionOnLineY = GetPointOnLine(
                second_line_point[0],
                second_line_point[1],
                first_line_point[0],
                first_line_point[1],
                realOffset,
            )

            startPositionX = second_line_point[0]
            startPositionY = second_line_point[1]
        elif ap == ARROW_POSITION_END:
            # If we're using a proportional offset, calculate just where this
            # will be on the line.
            realOffset = XOffset
            if proportionalOffset:
                totalLength = math.sqrt(
                    (second_last_line_point[0] - last_line_point[0])
                    * (second_last_line_point[0] - last_line_point[0])
                    + (second_last_line_point[1] - last_line_point[1])
                    * (second_last_line_point[1] - last_line_point[1])
                )
                realOffset = XOffset * totalLength

            positionOnLineX, positionOnLineY = GetPointOnLine(
                second_last_line_point[0],
                second_last_line_point[1],
                last_line_point[0],
                last_line_point[1],
                realOffset,
            )

            startPositionX = second_last_line_point[0]
            startPositionY = second_last_line_point[1]
        elif ap == ARROW_POSITION_MIDDLE:
            # Choose a point half way between the last and penultimate points
            x = (last_line_point[0] + second_last_line_point[0]) / 2.0
            y = (last_line_point[1] + second_last_line_point[1]) / 2.0

            # If we're using a proportional offset, calculate just where this
            # will be on the line.
            realOffset = XOffset
            if proportionalOffset:
                totalLength = math.sqrt(
                    (second_last_line_point[0] - x) * (second_last_line_point[0] - x)
                    + (second_last_line_point[1] - y) * (second_last_line_point[1] - y)
                )
                realOffset = XOffset * totalLength

            positionOnLineX, positionOnLineY = GetPointOnLine(
                second_last_line_point[0],
                second_last_line_point[1],
                x,
                y,
                realOffset,
            )
            startPositionX = second_last_line_point[0]
            startPositionY = second_last_line_point[1]

        # Add yOffset to arrow, if any

        # The translation that the y offset may give
        deltaX = 0.0
        deltaY = 0.0
        if arrow.GetYOffset and not self._ignoreArrowOffsets:
            #                             |(x4, y4)
            #                             |d
            #                             |
            #   (x1, y1)--------------(x3, y3)------------------(x2, y2)
            #   x4 = x3 - d * math.sin(theta)
            #   y4 = y3 + d * math.cos(theta)
            #
            #   Where theta = math.tan(-1) of (y3-y1) / (x3-x1)
            x1 = startPositionX
            y1 = startPositionY
            x3 = float(positionOnLineX)
            y3 = float(positionOnLineY)
            d = -arrow.GetYOffset()  # Negate so +offset is above line

            if x3 == x1:
                theta = math.pi / 2.0
            else:
                theta = math.atan((y3 - y1) / (x3 - x1))

            x4 = x3 - d * math.sin(theta)
            y4 = y3 + d * math.cos(theta)

            deltaX = x4 - positionOnLineX
            deltaY = y4 - positionOnLineY

        at = arrow._GetType()
        if at == ARROW_ARROW:
            arrowLength = arrow.GetSize()
            arrowWidth = arrowLength / 3.0

            tip_x, tip_y, side1_x, side1_y, side2_x, side2_y = GetArrowPoints(
                startPositionX + deltaX,
                startPositionY + deltaY,
                positionOnLineX + deltaX,
                positionOnLineY + deltaY,
                arrowLength,
                arrowWidth,
            )

            points = [
                (int(tip_x), int(tip_y)),
                (int(side1_x), int(side1_y)),
                (int(side2_x), int(side2_y)),
                (int(tip_x), int(tip_y)),
            ]

            pen = self._pen if self._pen else wx.Pen(wx.BLACK, 1, wx.PENSTYLE_SOLID)
            brush = self._brush if self._brush else wx.Brush(wx.BLACK, wx.BRUSHSTYLE_SOLID)
            dc.SetPen(pen)
            dc.SetBrush(brush)
            dc.DrawPolygon(points)
        elif at in [ARROW_HOLLOW_CIRCLE, ARROW_FILLED_CIRCLE]:
            # Find point on line of centre of circle, which is a radius away
            # from the end position
            diameter = arrow.GetSize()
            x, y = GetPointOnLine(
                startPositionX + deltaX,
                startPositionY + deltaY,
                positionOnLineX + deltaX,
                positionOnLineY + deltaY,
                diameter / 2.0,
            )
            x1 = int(x - diameter / 2.0)
            y1 = int(y - diameter / 2.0)
            pen = self._pen if self._pen else wx.Pen(wx.BLACK, 1, wx.PENSTYLE_SOLID)
            brush = self._brush if self._brush else wx.Brush(wx.BLACK, wx.BRUSHSTYLE_SOLID)
            dc.SetPen(pen)
            if arrow._GetType() == ARROW_HOLLOW_CIRCLE:
                dc.SetBrush(self.GetBackgroundBrush())
            else:
                dc.SetBrush(brush)

            dc.DrawEllipse(x1, y1, int(diameter), int(diameter))
        elif at == ARROW_SINGLE_OBLIQUE:
            pass
        elif at == ARROW_METAFILE:
            if arrow.GetMetaFile():
                # draw a metafile arrowhead (not currently used by wxdiagram)
                x, y = GetPointOnLine(
                    startPositionX,
                    startPositionY,
                    positionOnLineX,
                    positionOnLineY,
                    arrow.GetMetaFile()._width / 2.0,
                )
                x1 = startPositionX
                y1 = startPositionY
                x2 = float(positionOnLineX)
                y2 = float(positionOnLineY)

                theta = math.atan2(y2 - y1, x2 - x1) % (2 * math.pi)

                if arrow.GetMetaFile().GetRotateable():
                    arrow.GetMetaFile().Rotate(0.0, 0.0, theta)

                if self._erasing:
                    # If erasing, just draw a rectangle
                    minX, minY, maxX, maxY = arrow.GetMetaFile().GetBounds()
                    # Make erasing rectangle slightly bigger or you get droppings
                    extraPixels = 4
                    dc.DrawRectangle(
                        int(deltaX + x + minX - extraPixels / 2.0),
                        int(deltaY + y + minY - extraPixels / 2.0),
                        int(maxX - minX + extraPixels),
                        int(maxY - minY + extraPixels),
                    )
                else:
                    arrow.GetMetaFile().Draw(dc, int(x + deltaX), int(y + deltaY))

    def DrawArrows(self, dc):  # copied from site-packages/wx/lib/ogl/lines.py
        """Draw all arrows."""
        # Distance along line of each arrow: space them out evenly
        startArrowPos = 0.0
        endArrowPos = 0.0
        middleArrowPos = 0.0

        for arrow in self._arcArrows:
            ah = arrow.GetArrowEnd()
            if ah == ARROW_POSITION_START:
                if arrow.GetXOffset() and not self._ignoreArrowOffsets:
                    # If specified, x offset is proportional to line length
                    self.DrawArrow(dc, arrow, arrow.GetXOffset(), True)
                else:
                    self.DrawArrow(dc, arrow, startArrowPos, False)
                    startArrowPos += arrow.GetSize() + arrow.GetSpacing()
            elif ah == ARROW_POSITION_END:
                if arrow.GetXOffset() and not self._ignoreArrowOffsets:
                    self.DrawArrow(dc, arrow, arrow.GetXOffset(), True)
                else:
                    self.DrawArrow(dc, arrow, endArrowPos, False)
                    endArrowPos += arrow.GetSize() + arrow.GetSpacing()
            elif ah == ARROW_POSITION_MIDDLE:
                arrow.SetXOffset(middleArrowPos)
                if arrow.GetXOffset() and not self._ignoreArrowOffsets:
                    self.DrawArrow(dc, arrow, arrow.GetXOffset(), True)
                else:
                    self.DrawArrow(dc, arrow, middleArrowPos, False)
                    middleArrowPos += arrow.GetSize() + arrow.GetSpacing()

    # def OnDraw(self, dc):
    def draw(self, dc):
        """The draw handler."""
        # LineShapeOri.draw(self, dc)  # OGLLIKE normal line draw - TODO conflicts with wxogl style

        # print(f"Line2.draw, _lineControlPoints {self._lineControlPoints} whereas .x={self.x} .y={self.x}")
        if not self._lineControlPoints:
            return

        # Make ogllike xy points match the wx.ogl control points, so that low level ogllike
        # ResizeNodes position correctly.  Drawing of the line is done only based on wx.ogl control points
        # but positioning of ResizeNodes is done based on ogllike self.xy points
        self._sync_xy_from_control_points()

        """
        TODO make the two concepts 'self._lineControlPoints' and 'self.x/y points' the same,
        since an ogllike line is just the same as a bunch of
        wx.ogl control points, only (represented slightly differently).
        """

        if self._pen:
            dc.SetPen(self._pen)
        else:
            # Do not inherit whatever the previous shape left on the dc: the
            # labels below set a transparent pen, and the dashed-pen arrow line
            # would otherwise make later lines invisible/dashed.
            dc.SetPen(get_black_foreground_pen())
        if self._brush:
            dc.SetBrush(self._brush)
        else:
            dc.SetBrush(wx.TRANSPARENT_BRUSH)

        """
        https://discuss.wxpython.org/t/float-values-no-longer-accepted-in-wxpython-4-1-2a1-dev5259/35731

        You’re using Python 3.10 right? That’s a Python 3.10 change, not a
        change in wxPython. Methods that accept integers will no longer silently
        accept and truncate floats.

        Because wx.DCs use integer coordinates. In the wx.DC view of the world
        there is nothing between pixel (3,1) and (4,1) for example. If you need
        floating point sub-pixel precision then wx.GraphicsContext is available.

        The details for the change in Python are here: Issue 37999: No longer use
        implicit convertion to int with loss - Python tracker 25 https://bugs.python.org/issue37999
        A little searching will probably turn up more discussion about it.

        Our solution: use integers for all drawing operations by adding `int()`
        """
        points = []
        for point in self._lineControlPoints:
            points.append(wx.Point(int(point[0]), int(point[1])))  # python 3.10 needs ints

        if self._isSpline:
            dc.DrawSpline(points)
        else:
            dc.DrawLines(points)

        if sys.platform[:3] == "win":
            # For some reason, last point isn't drawn under Windows
            pt = points[-1]
            dc.DrawPoint(pt[0], pt[1])

        # Problem with pen - if not a solid pen, does strange things
        # to the arrowhead. So make (get) a new pen that's solid.
        if self._pen and self._pen.GetStyle() != wx.PENSTYLE_SOLID:
            solid_pen = wx.Pen(self._pen.GetColour(), 1, wx.PENSTYLE_SOLID)
            if solid_pen:
                dc.SetPen(solid_pen)

        self.DrawArrows(dc)
        self.DrawLabels(dc)

    # --- Labels -------------------------------------------------------------

    def AddText(self, string, position=0):
        """Add a label line to a line region.

        ``position`` is 0 for the middle of the line (the default), 1 for near
        the start and 2 for near the end.
        """
        region = self._regions[position]
        text = region.GetText()
        text = f"{text}\n{string}" if text else string
        self.SetLabelText(position, text)

    def SetLabelText(self, position, text):
        """Replace the label text of one line region."""
        region = self._regions[position]
        region.SetText(text)
        region.ClearText()
        for line in text.split("\n"):
            region.GetFormattedText().append(ShapeTextLine(0, 0, line))
        self._labelRects.pop(position, None)

    def SetLabelPosition(self, position, x, y):
        """Offset a label from its default point on the line."""
        self._regions[position].SetPosition(x, y)
        self._labelRects.pop(position, None)

    def _label_lines(self, position):
        region = self._regions[position]
        lines = [line.GetText() for line in region.GetFormattedText()]
        if not lines:
            text = region.GetText()
            lines = text.split("\n") if text else []
        return lines

    def _point_along(self, fraction):
        """Point at ``fraction`` of the line's length (chords for splines)."""
        points = self._lineControlPoints
        if not points:
            return self.GetX(), self.GetY()
        if len(points) == 1:
            return points[0][0], points[0][1]

        segments = []
        total = 0.0
        for first, second in zip(points, points[1:]):
            length = math.hypot(second[0] - first[0], second[1] - first[1])
            segments.append((first, second, length))
            total += length
        if total <= 0:
            return points[0][0], points[0][1]

        target = total * fraction
        walked = 0.0
        for first, second, length in segments:
            if length > 0 and walked + length >= target:
                t = (target - walked) / length
                return (
                    first[0] + (second[0] - first[0]) * t,
                    first[1] + (second[1] - first[1]) * t,
                )
            walked += length
        return points[-1][0], points[-1][1]

    def GetLabelPosition(self, position):
        """Return the label anchor in diagram coordinates."""
        base_x, base_y = self._point_along((0.5, 0.15, 0.85)[position])
        offset_x, offset_y = self._regions[position].GetPosition()
        return base_x + offset_x, base_y + offset_y

    def DrawLabels(self, dc):
        """Draw the line's labels and remember their rectangles for hit-testing."""
        for position in range(3):
            lines = self._label_lines(position)
            if not lines:
                self._labelRects.pop(position, None)
                continue
            region = self._regions[position]
            font = region.GetFont()
            if font:
                dc.SetFont(font)
            dc.SetTextForeground(region.GetActualColourObject())

            extents = [dc.GetTextExtent(line) for line in lines]
            width = max(extent[0] for extent in extents)
            height = sum(extent[1] for extent in extents)
            centre_x, centre_y = self.GetLabelPosition(position)
            pad = 2

            background = wx.WHITE
            canvas = self.GetCanvas()
            if canvas is not None:
                background = canvas.GetBackgroundColour()
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.Brush(background))
            left = centre_x - width / 2.0 - pad
            top = centre_y - height / 2.0 - pad
            dc.DrawRectangle(int(left), int(top), int(width + 2 * pad), int(height + 2 * pad))
            self._labelRects[position] = (
                left,
                top,
                left + width + 2 * pad,
                top + height + 2 * pad,
            )

            text_y = centre_y - height / 2.0
            for line, (line_w, line_h) in zip(lines, extents):
                dc.DrawText(line, int(centre_x - line_w / 2.0), int(text_y))
                text_y += line_h

    def OnDrawControlPoints(self, dc):
        """The draw control points handler."""
        if not self._drawHandles:
            return

        # Draw temporary label rectangles if necessary
        for i in range(3):
            if self._labelObjects[i]:
                self._labelObjects[i].Draw(dc)

        # ANDY
        # Shape.OnDrawControlPoints(self, dc)

    def OnEraseControlPoints(self, dc):
        """The erase control points handler."""
        # Erase temporary label rectangles if necessary

        for i in range(3):
            if self._labelObjects[i]:
                self._labelObjects[i].Erase(dc)

        # ANDY
        # Shape.OnEraseControlPoints(self, dc)

    def ResetControlPoints(self):
        """Reset the control points."""
        if self._canvas and self._lineControlPoints and self._controlPoints:
            for i in range(min(len(self._controlPoints), len(self._lineControlPoints))):
                point = self._lineControlPoints[i]
                control = self._controlPoints[i]
                control.SetX(point[0])
                control.SetY(point[1])

    # more OGLLIKE extras for LineShape to make it more like wx.lib.ogl

    def ClearRegions(self):
        """Clear the ShapeRegions from the shape."""
        self._regions = []

    def AddRegion(self, region):
        """Add a region to the shape."""
        self._regions.append(region)

    def AddArrow(
        self, type, end=ARROW_POSITION_END, size=10.0, xOffset=0.0, name="", mf=None, arrowId=-1
    ):
        """
        Add an arrow (or annotation) to the line.

        :param `type`: an arrow head type, one of the following

         ======================================== ==================================
         Arrow head type                          Description
         ======================================== ==================================
         `ARROW_HOLLOW_CIRCLE`                    a hollow circle
         `ARROW_FILLED_CIRCLE`                    a filled circle
         `ARROW_ARROW`                            an arrow
         `ARROW_SINGLE_OBLIQUE`                   a single oblique
         `ARROW_DOUBLE_OBLIQUE`                   a double oblique
         `ARROW_METAFILE`                         custom, define in metafile
         ======================================== ==================================

        :param `end`: may be one of the following

         ======================================== ==================================
         Arrow head type                          Description
         ======================================== ==================================
         `ARROW_POSITION_END`                     arrow appears at the end
         `ARROW_POSITION_START`                   arrow appears at the start
         ======================================== ==================================

        :param `size`: specifies the lenght of the arrow
        :param `xOffset`: specifies the offset from the end of the line
        :param `name`: specifies a name
        :param `mf`: mf can be a wxPseduoMetaFile, perhaps loaded from a simple Windows
          metafile.
        :param `arrowId`: the id for the arrow

        """
        arrow = ArrowHead(type, end, size, xOffset, name, mf, arrowId)
        self._arcArrows.append(arrow)
        return arrow

    def AddArrowOrdered(self, arrow, reference_list, end):
        """Insert an arrowhead in the order defined by ``reference_list``."""
        if not reference_list:
            return False

        target_name = arrow.GetName()
        if reference_list[0].GetName() == target_name:
            self._arcArrows.insert(0, arrow)
            return True

        i1 = i2 = 0
        while i1 < len(reference_list) and i2 < len(self._arcArrows):
            ref_arrow = reference_list[i1]
            current_arrow = self._arcArrows[i2]
            if (
                current_arrow.GetArrowEnd() == end
                and current_arrow.GetName() == ref_arrow.GetName()
            ):
                i2 += 1
            if target_name == ref_arrow.GetName():
                if i2 < len(self._arcArrows):
                    self._arcArrows.insert(i2, arrow)
                else:
                    self._arcArrows.append(arrow)
                return True
            i1 += 1

        self._arcArrows.append(arrow)
        return True

    def GetArrows(self):
        """Return the line's arrowheads."""
        return self._arcArrows

    def ClearArrow(self, name):
        """Delete the arrowhead with the given name."""
        for arrow in self._arcArrows:
            if arrow.GetName() == name:
                self._arcArrows.remove(arrow)
                return True
        return False

    def FindArrowHead(self, position, name):
        """Find an arrowhead by position and name (position -1 matches any)."""
        for arrow in self._arcArrows:
            if (position == -1 or position == arrow.GetArrowEnd()) and arrow.GetName() == name:
                return arrow
        return None

    def FindArrowHeadId(self, arrow_id):
        """Find an arrowhead by id."""
        for arrow in self._arcArrows:
            if arrow_id == arrow.GetId():
                return arrow
        return None

    def DeleteArrowHead(self, position, name):
        """Delete an arrowhead by position and name (position -1 matches any)."""
        for arrow in self._arcArrows:
            if (position == -1 or position == arrow.GetArrowEnd()) and arrow.GetName() == name:
                self._arcArrows.remove(arrow)
                return True
        return False

    def DeleteArrowHeadId(self, arrow_id):
        """Delete an arrowhead by id."""
        for arrow in self._arcArrows:
            if arrow_id == arrow.GetId():
                self._arcArrows.remove(arrow)
                return True
        return False

    def SetIgnoreOffsets(self, ignore):
        """Set whether arrow offsets from the line ends are ignored."""
        self._ignoreArrowOffsets = ignore

    def SetSpline(self, spline):
        """Draw a spline through the control points when True."""
        self._isSpline = spline

    def IsSpline(self):
        """Return True when the line is drawn as a spline."""
        return self._isSpline

    def Straighten(self, dc=None):
        """Straighten vertical and horizontal segments of the line."""
        if len(self._lineControlPoints) < 3:
            return

        if dc:
            self.Erase(dc)

        GraphicsStraightenLine(self._lineControlPoints[-1], self._lineControlPoints[-2])
        for i in range(len(self._lineControlPoints) - 2):
            GraphicsStraightenLine(self._lineControlPoints[i], self._lineControlPoints[i + 1])

        if dc:
            self.draw(dc)

    #######

    # def draw(self, dc):  # local ogl version of OnDraw, the draw handler
    #     super().draw(dc)
    #     self.DrawArrows(dc)

    # ANDY ADDED

    def SetTo(self, object):
        """Set the 'to' object for the line."""
        self._to = object

    def SetFrom(self, object):
        """Set the 'from' object for the line."""
        self._from = object

    def GetFrom(self):
        """Return the shape at the start of the line."""
        return self._from

    def GetTo(self):
        """Return the shape at the end of the line."""
        return self._to

    def MakeLineControlPoints(self, n):
        """
        Make a given number of control points.

        :param int `n`: number of control points, minimum of two

        """
        self._lineControlPoints = []

        for _ in range(n):
            point = wx.RealPoint(-999, -999)
            self._lineControlPoints.append(point)

        # pi: added _initialised to keep track of when we have set
        # the middle points to something other than (-999, -999)
        self._initialised = False

    def Initialise(self):
        """Replace any placeholder control points with midpoints.

        Fresh control points start at (-999, -999); promote them to the
        midpoint of the line so routing has sane values to work from.
        """
        if self._lineControlPoints:
            # Just move the first and last control points
            first_point = self._lineControlPoints[0]
            last_point = self._lineControlPoints[-1]

            # If any of the line points are at -999, we must
            # initialize them by placing them half way between the first
            # and the last.
            for i in range(1, len(self._lineControlPoints)):
                point = self._lineControlPoints[i]
                if point[0] == -999:
                    if first_point[0] < last_point[0]:
                        x1 = first_point[0]
                        x2 = last_point[0]
                    else:
                        x2 = first_point[0]
                        x1 = last_point[0]
                    if first_point[1] < last_point[1]:
                        y1 = first_point[1]
                        y2 = last_point[1]
                    else:
                        y2 = first_point[1]
                        y1 = last_point[1]
                    self._lineControlPoints[i] = wx.RealPoint(
                        (x2 - x1) / 2.0 + x1, (y2 - y1) / 2.0 + y1
                    )
            self._initialised = True

    def _sync_xy_from_control_points(self):
        """Make the ogllike ``x``/``y`` point lists agree with the wx.ogl
        control points.

        ``x``/``y`` are what hit tests and selection handles use, while the
        control points are what is actually drawn and what ``SetEnds`` stores.
        Keeping two representations is unfortunate, but they must never drift
        apart: the draw code rebuilds one from the other, so a write to the
        wrong one is silently lost.
        """
        if self._lineControlPoints:
            self.x, self.y = line_control_points_to_xy_points(self._lineControlPoints)

    def SetEnds(self, x1, y1, x2, y2):
        """
        Set the end positions of the line.

        :param: `x1`: x1 position
        :param: `y1`: y1 position
        :param: `x2`: x2 position
        :param: `y2`: y2 position


        """
        self._lineControlPoints[0] = wx.RealPoint(x1, y1)
        self._lineControlPoints[-1] = wx.RealPoint(x2, y2)
        self._sync_xy_from_control_points()

    # Get absolute positions of ends
    def GetEnds(self):
        """Get the visible endpoints of the lines for drawing between two objects."""
        first_point = self._lineControlPoints[0]
        last_point = self._lineControlPoints[-1]

        return first_point[0], first_point[1], last_point[0], last_point[1]

    def SetAttachments(self, from_attach, to_attach):
        """
        Specify which object attachment points should be used at each end of the line.

        :param `from_attach`: the from points ???
        :param `to_attach`: the to points ???

        """
        self._attachmentFrom = from_attach
        self._attachmentTo = to_attach

    def move(self, x, y):
        """Relative move of the whole line.

        The control points are the source of truth, so move those and then
        refresh ``x``/``y``; moving only ``x``/``y`` would be undone by the
        next repaint.
        """
        if not self._lineControlPoints:
            return
        for point in self._lineControlPoints:
            point[0] = point[0] + x
            point[1] = point[1] + y
        self._sync_xy_from_control_points()

    def move_handle(self, index, dx, dy, free_aspect=False, from_center=False):
        """Move one control point (used when dragging a line's handle).

        Returns True if the point was moved.
        """
        if not self._lineControlPoints or index >= len(self._lineControlPoints):
            return False
        point = self._lineControlPoints[index]
        point[0] = point[0] + dx
        point[1] = point[1] + dy
        self._sync_xy_from_control_points()
        return True

    def OnMoveLink(self, dc, moveControlPoints=True):
        """The move linke handler, called when a connected object has moved, to move the link to
        correct position.
        """
        if not self._from or not self._to:
            return

        # Do each end - nothing in the middle. User has to move other points
        # manually if necessary
        end_x, end_y, other_end_x, other_end_y = self.FindLineEndPoints()

        oldX, oldY = self._xpos, self._ypos

        # pi: The first time we go through FindLineEndPoints we can't
        # use the middle points (since they don't have sane values),
        # so we just do what we do for a normal line. Then we call
        # Initialise to set the middle points, and then FindLineEndPoints
        # again, but this time (and from now on) we use the middle
        # points to calculate the end points.
        # This was buggy in the C++ version too.

        self.SetEnds(end_x, end_y, other_end_x, other_end_y)

        if len(self._lineControlPoints) > 2:
            self.Initialise()

        # Do a second time, because one may depend on the other
        end_x, end_y, other_end_x, other_end_y = self.FindLineEndPoints()
        self.SetEnds(end_x, end_y, other_end_x, other_end_y)

        # Try to move control points with the arc
        x_offset = self._xpos - oldX
        y_offset = self._ypos - oldY

        # Only move control points if it's a self link. And only works
        # if attachment mode is ON
        if (
            self._from == self._to
            and self._from.GetAttachmentMode() != ATTACHMENT_MODE_NONE
            and moveControlPoints
            and self._lineControlPoints
            and not (x_offset == 0 and y_offset == 0)
        ):
            for point in self._lineControlPoints[1:-1]:
                point[0] += x_offset
                point[1] += y_offset

        self.Move(dc, self._xpos, self._ypos)
        self.UpdateRoute()

    def UpdateRoute(self):
        """Route the line around foreign rectangles when ``autoRoute`` is on.

        Returns the routing style (``straight``, ``curved`` or ``orthogonal``),
        or None when routing does not apply.  Endpoint clipping is recomputed
        from a straight line first, so a previous curve cannot feed back into
        the next route.
        """
        if (
            not self.autoRoute
            or self._from is None
            or self._to is None
            or self._from is self._to
            or not self._lineControlPoints
        ):
            return None
        canvas = self.GetCanvas()
        diagram = getattr(canvas, "diagram", None) if canvas is not None else None
        if diagram is None:
            return None

        # Collapse to a straight line so FindLineEndPoints clips along the
        # shape-to-shape direction rather than the previous curve's tangent.
        self.MakeLineControlPoints(2)
        ends = self.FindLineEndPoints()
        if not ends:
            return None
        self.SetEnds(*ends)

        obstacles = []
        for shape in diagram.shapes:
            if shape is self or shape is self._from or shape is self._to:
                continue
            if isinstance(shape, RectangleShape) and len(shape.x) == 2 and len(shape.y) == 2:
                obstacles.append((shape.x[0], shape.y[0], shape.x[1], shape.y[1]))

        start = (self._lineControlPoints[0][0], self._lineControlPoints[0][1])
        end = (self._lineControlPoints[-1][0], self._lineControlPoints[-1][1])
        points, style = routing.route_edge(
            start,
            end,
            obstacles,
            spread=self._lane_offset(),
            prefer_curve=self.autoRoute == "curved",
            start_normal=self._endpoint_normal(start, self._from),
            end_normal=self._endpoint_normal(end, self._to),
        )
        if len(points) != len(self._lineControlPoints):
            self.MakeLineControlPoints(len(points))
        for control, point in zip(self._lineControlPoints, points):
            control[0] = point[0]
            control[1] = point[1]
        self.SetSpline(style == "curved")
        self._sync_xy_from_control_points()
        return style

    def SetRouteMode(self, mode):
        """Set how the edge is drawn: ``"straight"``, ``"avoid"`` or ``"curved"``.

        ``straight`` collapses back to an attached two-point line (any manual
        bend is dropped); ``avoid`` bends only when a box is in the way;
        ``curved`` always bows into a spline.
        """
        if mode not in ("straight", "avoid", "curved"):
            raise ValueError(f"Unknown route mode: {mode!r}")
        self.autoRoute = {"straight": False, "avoid": True, "curved": "curved"}[mode]
        if self.autoRoute:
            self.UpdateRoute()
        else:
            self.ResetRoute()
        canvas = self.GetCanvas()
        if canvas is not None:
            canvas.Refresh()

    def GetRouteMode(self):
        """Return the current routing mode (see :meth:`SetRouteMode`)."""
        if self.autoRoute == "curved":
            return "curved"
        return "avoid" if self.autoRoute else "straight"

    def ResetRoute(self):
        """Collapse the edge to a straight, attached two-point line."""
        if not self._lineControlPoints:
            return
        if len(self._lineControlPoints) > 2:
            start = (self._lineControlPoints[0][0], self._lineControlPoints[0][1])
            end = (self._lineControlPoints[-1][0], self._lineControlPoints[-1][1])
            self.MakeLineControlPoints(2)
            self._lineControlPoints[0][0], self._lineControlPoints[0][1] = start
            self._lineControlPoints[1][0], self._lineControlPoints[1][1] = end
        if self._from is not None and self._to is not None:
            ends = self.FindLineEndPoints()
            if ends:
                self.SetEnds(*ends)
        self.SetSpline(False)
        self._sync_xy_from_control_points()

    @staticmethod
    def _endpoint_normal(point, shape):
        """Outward normal of the shape side the clipped endpoint sits on."""
        if not isinstance(shape, RectangleShape) or len(shape.x) != 2 or len(shape.y) != 2:
            return None
        distances = (
            (abs(point[0] - shape.x[0]), (-1.0, 0.0)),
            (abs(point[0] - shape.x[1]), (1.0, 0.0)),
            (abs(point[1] - shape.y[0]), (0.0, -1.0)),
            (abs(point[1] - shape.y[1]), (0.0, 1.0)),
        )
        return min(distances, key=lambda item: item[0])[1]

    def _lane_offset(self, spacing=14.0):
        """Sideways offset for parallel edges between the same two shapes."""
        canvas = self.GetCanvas()
        diagram = getattr(canvas, "diagram", None) if canvas is not None else None
        if diagram is None or self._from is None or self._to is None:
            return 0.0
        peers = [
            shape
            for shape in diagram.shapes
            if isinstance(shape, LineShape)
            and shape is not self
            and shape._from is not None
            and shape._to is not None
            and (
                (shape._from is self._from and shape._to is self._to)
                or (shape._from is self._to and shape._to is self._from)
            )
        ]
        group = sorted(peers + [self], key=lambda line: (line.GetId(), id(line)))
        index = group.index(self)
        return (index - (len(group) - 1) / 2.0) * spacing

    def FindLineEndPoints(self):
        """
        Finds the x, y points at the two ends of the line.

        This function can be used by e.g. line-routing routines to
        get the actual points on the two node images where the lines will be
        drawn to / from.
        """
        if not self._from or not self._to:
            return

        # Do each end - nothing in the middle. User has to move other points
        # manually if necessary.
        second_point = self._lineControlPoints[1]
        second_last_point = self._lineControlPoints[-2]

        # pi: If we have a segmented line and this is the first time,
        # do this as a straight line.
        if len(self._lineControlPoints) > 2 and self._initialised:
            if self._from.GetAttachmentMode() != ATTACHMENT_MODE_NONE:
                nth, no_arcs = self.FindNth(self._from, False)  # Not incoming
                end_x, end_y = self._from.GetAttachmentPosition(
                    self._attachmentFrom, nth, no_arcs, self
                )
            else:
                end_x, end_y = self._from.GetPerimeterPoint(
                    self._from.GetX(), self._from.GetY(), second_point[0], second_point[1]
                )

            if self._to.GetAttachmentMode() != ATTACHMENT_MODE_NONE:
                nth, no_arch = self.FindNth(self._to, True)  # Incoming
                other_end_x, other_end_y = self._to.GetAttachmentPosition(
                    self._attachmentTo, nth, no_arch, self
                )
            else:
                other_end_x, other_end_y = self._to.GetPerimeterPoint(
                    self._to.GetX(), self._to.GetY(), second_last_point[0], second_last_point[1]
                )
        else:
            fromX = self._from.GetX()
            fromY = self._from.GetY()
            toX = self._to.GetX()
            toY = self._to.GetY()

            if self._from.GetAttachmentMode() != ATTACHMENT_MODE_NONE:
                nth, no_arcs = self.FindNth(self._from, False)
                end_x, end_y = self._from.GetAttachmentPosition(
                    self._attachmentFrom, nth, no_arcs, self
                )
                fromX = end_x
                fromY = end_y

            if self._to.GetAttachmentMode() != ATTACHMENT_MODE_NONE:
                nth, no_arcs = self.FindNth(self._to, True)
                other_end_x, other_end_y = self._to.GetAttachmentPosition(
                    self._attachmentTo, nth, no_arcs, self
                )
                toX = other_end_x
                toY = other_end_y

            if self._from.GetAttachmentMode() == ATTACHMENT_MODE_NONE:
                end_x, end_y = self._from.GetPerimeterPoint(
                    self._from.GetX(), self._from.GetY(), toX, toY
                )

            if self._to.GetAttachmentMode() == ATTACHMENT_MODE_NONE:
                other_end_x, other_end_y = self._to.GetPerimeterPoint(
                    self._to.GetX(), self._to.GetY(), fromX, fromY
                )

        return end_x, end_y, other_end_x, other_end_y

    def GetBoundingBoxMin(self):
        """Get the minimum bounding box."""
        x1, y1 = 10000, 10000
        x2, y2 = -10000, -10000

        for point in self._lineControlPoints:
            if point[0] < x1:
                x1 = point[0]
            if point[1] < y1:
                y1 = point[1]
            if point[0] > x2:
                x2 = point[0]
            if point[1] > y2:
                y2 = point[1]

        return x2 - x1, y2 - y1

    def Delete(self):
        """Delete the line, unlink it first."""
        self.Unlink()
        Shape.Delete(self)

    def Unlink(self):
        """Unlink the line from the nodes at either end."""
        if self._to:
            self._to.GetLines().remove(self)
        if self._from:
            self._from.GetLines().remove(self)
        self._to = None
        self._from = None
        # for i in range(3):
        #     if self._labelObjects[i]:
        #         self._labelObjects[i].Select(False)
        #         self._labelObjects[i].RemoveFromCanvas(self._canvas)
        self.ClearArrowsAtPosition(-1)

    def ClearArrowsAtPosition(self, end):
        """
        Delete the arrows at the specified position, or at any position if position is -1.

        :param `end`: position to clear arrow from

        """
        if end == -1:
            self._arcArrows = []
            return

        for arrow in self._arcArrows:
            if arrow.GetArrowEnd() == end:
                self._arcArrows.remove(arrow)

    def OnSelect(self, event):
        # print("selected line", self, self._lineControlPoints, self.x, self.y)
        # Let's make ogllike line dimensions the same as the line control points - don't like
        # these zero dimension shapes.  Plus ogllike canvas will put the resize nodes at the
        # centre, which is silly.
        self._sync_xy_from_control_points()

    # ANDY: Override the normal lineshape hit test because
    # lines built via wx.ogl technique because these lines have zero dimension
    # and their dimension only exists through their control points.
    def HitTest(self, x, y):
        """
        Line hit test.

        :param `x`: x position
        :param `y`: y position

        """
        if not self._lineControlPoints:
            return False

        # Labels sit on or near the line and are clickable as well.  The
        # rectangles are cached by DrawLabels (paint happens before clicks).
        for rect in self._labelRects.values():
            if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                return (0, 0.0)

        for i in range(len(self._lineControlPoints) - 1):
            point1 = self._lineControlPoints[i]
            point2 = self._lineControlPoints[i + 1]

            # For inaccurate mousing allow 8 pixel corridor
            extra = 4

            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]

            seg_len = math.sqrt(dx * dx + dy * dy)
            if dy == 0 and dx == 0:
                continue
            distance_from_seg = (
                seg_len * float((x - point1[0]) * dy - (y - point1[1]) * dx) / (dy * dy + dx * dx)
            )
            distance_from_prev = (
                seg_len * float((y - point1[1]) * dy + (x - point1[0]) * dx) / (dy * dy + dx * dx)
            )

            if (
                abs(distance_from_seg) < extra
                and distance_from_prev >= 0
                and distance_from_prev <= seg_len
            ):
                return 0, distance_from_seg

        return False


# WARNING - these haven't been converted into ogllike draw() etc


class ArrowHead(object):
    """
    The arrow head class.
    """

    def __init__(self, type=0, end=0, size=0.0, dist=0.0, name="", mf=None, arrowId=-1):
        """
        Default class constructor.

        :param int `type`: the type

         ======================================== ==================================
         Arrow head type                          Description
         ======================================== ==================================
         `ARROW_HOLLOW_CIRCLE`                    a hollow circle
         `ARROW_FILLED_CIRCLE`                    a filled circle
         `ARROW_ARROW`                            an arrow
         `ARROW_SINGLE_OBLIQUE`                   a single oblique
         `ARROW_DOUBLE_OBLIQUE`                   a double oblique
         `ARROW_METAFILE`                         custom, define in metafile
         ======================================== ==================================

        :param int `end`: end of arrow head ???
        :param float `size`: size of arrow head
        :param float `dist`: dist ???
        :param string `name`: name of arrow head
        :param `mf`: mf ???
        :param `arrowId`: id of arrow head

        """
        if isinstance(type, ArrowHead):
            pass
        else:
            self._arrowType = type
            self._arrowEnd = end
            self._arrowSize = size
            self._xOffset = dist
            self._yOffset = 0.0
            self._spacing = 5.0

            self._arrowName = name
            self._metaFile = mf
            self._id = arrowId
            if self._id == -1:
                self._id = wx.NewIdRef()

    def _GetType(self):
        return self._arrowType

    def GetPosition(self):
        """Get end position."""
        return self._arrowEnd

    def SetPosition(self, pos):
        """Set end position.

        :param `pos`: position to set it to
        """
        self._arrowEnd = pos

    def GetXOffset(self):
        """Get the X offset."""
        return self._xOffset

    def GetYOffset(self):
        """Get the Y offset."""
        return self._yOffset

    def GetSpacing(self):
        """Get the spacing."""
        return self._spacing

    def GetSize(self):
        """Get the arrow size."""
        return self._arrowSize

    def SetSize(self, size):
        """Set the arrow size.

        :param `size`: size in points???

        :note: if a custom arrow is used size is used to scale the arrow???
        """
        self._arrowSize = size
        if self._arrowType == ARROW_METAFILE and self._metaFile:
            oldWidth = self._metaFile._width
            if oldWidth == 0:
                return

            scale = float(size) / oldWidth
            if scale != 1:
                self._metaFile.Scale(scale, scale)

    def GetName(self):
        """Get the arrow name."""
        return self._arrowName

    def SetXOffset(self, x):
        """Set the X offset.

        :param `x`: value to set the offset to???
        """
        self._xOffset = x

    def SetYOffset(self, y):
        """Set the Y offset.

        :param `y`: value to set the offset to???
        """
        self._yOffset = y

    def GetMetaFile(self):
        """Get the metafile."""
        return self._metaFile

    def GetId(self):
        """Get the id."""
        return self._id

    def GetArrowEnd(self):
        """Get the arrow end position."""
        return self._arrowEnd

    def GetArrowSize(self):
        """Get the arrow size."""
        return self._arrowSize

    def SetSpacing(self, sp):
        """Set the spacing.

        :param `sp`: the new spacing value
        """
        self._spacing = sp


class ControlPoint(RectangleShape):
    """The :class:`wx.ControlPoint` class."""

    def __init__(self, theCanvas, object, size, the_xoffset, the_yoffset, the_type):
        """
        Default class constructor

        :param `theCanvas`: a :class:`~lib.ogl.Canvas`
        :param `object`: the shape, instance of :class:`~lib.ogl.Shape`
        :param float `size`: the size
        :param float `the_xoffset`: the x position
        :param float `the_yoffset`: the y position
        :param int `the_type`: one of the following types ???

         ======================================== ==================================
         Control point type                       Description
         ======================================== ==================================
         `CONTROL_POINT_VERTICAL`                 Vertical
         `CONTROL_POINT_HORIZONTAL`               Horizontal
         `CONTROL_POINT_DIAGONAL`                 Diagonal
         ======================================== ==================================

        """
        RectangleShape.__init__(self, size, size)

        self._canvas = theCanvas
        self._shape = object
        self._xoffset = the_xoffset
        self._yoffset = the_yoffset
        self._type = the_type
        self.SetPen(get_black_foreground_pen())
        self.SetBrush(wx.BLACK_BRUSH)
        self._oldCursor = None
        self._visible = True
        self._eraseObject = True

    # Don't even attempt to draw any text - waste of time
    def OnDrawContents(self, dc):
        """not implemented???"""
        pass

    def OnDraw(self, dc):
        """The draw handler."""
        self._xpos = self._shape.GetX() + self._xoffset
        self._ypos = self._shape.GetY() + self._yoffset
        RectangleShape.OnDraw(self, dc)

    def OnErase(self, dc):
        """The erase handler."""
        RectangleShape.OnErase(self, dc)

    # Implement resizing of canvas object
    def OnDragLeft(self, draw, x, y, keys=0, attachment=0):
        """The drag left handler."""
        self._shape.GetEventHandler().OnSizingDragLeft(self, draw, x, y, keys, attachment)

    def OnBeginDragLeft(self, x, y, keys=0, attachment=0):
        """The begin drag left handler."""
        self._shape.GetEventHandler().OnSizingBeginDragLeft(self, x, y, keys, attachment)

    def OnEndDragLeft(self, x, y, keys=0, attachment=0):
        """The end drag left handler."""
        self._shape.GetEventHandler().OnSizingEndDragLeft(self, x, y, keys, attachment)

    def GetNumberOfAttachments(self):
        """Get the number of attachments."""
        return 1

    def GetAttachmentPosition(self, attachment, nth=0, no_arcs=1, line=None):
        """
        Get the attachment position.

        :param `attachment`: the attachment ???
        :param `nth`: get nth attachment ???
        :param `no_arcs`: ???
        :param `line`: ???

        """
        return self._xpos, self._ypos

    def SetEraseObject(self, er):
        """
        Set the erase object ???

        :param `er`: the object

        """
        self._eraseObject = er


class LineControlPoint(ControlPoint):
    """
    The :class:`LineControlPoint` class.
    """

    def __init__(self, theCanvas=None, object=None, size=0.0, x=0.0, y=0.0, the_type=0):
        """
        Default class constructor.

        :param `theCanvas`: a :class:`~lib.ogl.Canvas`
        :param `object`: not used ???
        :param float `size`: the size
        :param float `x`: the x position
        :param float `y`: the y position
        :param int `the_type`: one of the following types

         ======================================== ==================================
         Control point type                       Description
         ======================================== ==================================
         `CONTROL_POINT_VERTICAL`                 Vertical
         `CONTROL_POINT_HORIZONTAL`               Horizontal
         `CONTROL_POINT_DIAGONAL`                 Diagonal
         ======================================== ==================================

        """
        ControlPoint.__init__(self, theCanvas, object, size, x, y, the_type)
        self._xpos = x
        self._ypos = y
        self._type = the_type
        self._point = None
        self._originalPos = None

    def OnDraw(self, dc):
        """The draw handler."""
        RectangleShape.OnDraw(self, dc)

    # Implement movement of Line point
    def OnDragLeft(self, draw, x, y, keys=0, attachment=0):
        """The drag left handler."""
        self._shape.GetEventHandler().OnSizingDragLeft(self, draw, x, y, keys, attachment)

    def OnBeginDragLeft(self, x, y, keys=0, attachment=0):
        """The begin drag left handler."""
        self._shape.GetEventHandler().OnSizingBeginDragLeft(self, x, y, keys, attachment)

    def OnEndDragLeft(self, x, y, keys=0, attachment=0):
        """The end drag left handler."""
        self._shape.GetEventHandler().OnSizingEndDragLeft(self, x, y, keys, attachment)


__all__ = ["LineShape", "ArrowHead", "ControlPoint", "LineControlPoint"]
