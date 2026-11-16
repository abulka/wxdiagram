# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         divided.py
#
# Author:       Pierre Hjälm (from C++ original by Julian Smart)
#               Andy Bulka - portions extracted, altered or deleted to suit ogllike and pynsource
#
# Created:      2004-05-08
# Copyright:    (c) 2004 Pierre Hjälm - 1998 Julian Smart
# Licence:      wxWindows license
# Tags:         phoenix-port, unittest, py3-port, documented
# ----------------------------------------------------------------------------

import wx
from .core import RectangleShape, Connectable, Resizeable, Selectable, Attributable
from .geometry import DrawFormattedText


# class DividedShape(RectangleShape):
class DividedShape(RectangleShape, Connectable, Resizeable, Selectable, Attributable):
    """
    A :class:`DividedShape` is a rectangle with a number of vertical divisions.
    Each division may have its text formatted with independent characteristics,
    and the size of each division relative to the whole image may be specified.
    """

    def __init__(self, w, h):
        """
        Default class constructor.

        :param `w`: width of rectangle
        :param `h`: heigth of rectangle

        """
        top = 0
        left = 0
        RectangleShape.__init__(self, top, left, top + w, left + h)

        # ANDY #####
        Resizeable.__init__(self)
        Connectable.__init__(self)
        Attributable.__init__(self)

        self.ClearRegions()

    # real OGL uses OnDraw(), ogllike uses draw()

    # def OnDraw(self, dc):
    #     """The draw handler."""
    #     RectangleShape.OnDraw(self, dc)

    # ANDY #####

    def SetFont(self, the_font, regionId=0):
        """
        Set the font for the specified text region.

        :param `the_font`: an instance of :class:`wx.Font` ???
        :param `regionId`: the region identifier

        """
        self._font = the_font
        if regionId < len(self._regions):
            self._regions[regionId].SetFont(the_font)

    def OnLeftDown(self, event):
        pass

    def draw(self, dc):
        """The draw handler."""
        RectangleShape.draw(self, dc)

        # # Andy's simple multi-line text drawing :-) is a bit dodgy
        # MARGIN = 2
        # last_y = self.y[0] + MARGIN
        # last_height = self._height
        # msg = "hi there\nworld earth\nI hope things are ok"
        # for line in msg.split("\n"):
        #     w, h = dc.GetTextExtent(msg)
        #     # mx = int((self.x[0] + self.x[1]) / 2.0) - int(w / 2.0)
        #     # my = int((self.y[0] + self.y[1]) / 2.0) - int(h / 2.0)
        #     mx = self.x[0] - self._width + MARGIN # weird, have to subtract width?
        #     my = last_y - last_height # weird, have to subtract height?
        #     dc.DrawText(msg, mx, my)
        #     last_y = my
        #     last_height = 0

        # COMPLEX OGL formatted text stuff.
        #
        self.OnDrawContents(
            dc
        )  # ANDY - in real ogl this call is triggered via composite shape stuff

    def OnDrawContents(self, dc):
        """The draw contents handler."""
        if self.GetRegions():
            defaultProportion = 1.0 / len(self.GetRegions())
        else:
            defaultProportion = 0.0
        currentY = self._ypos - self._height / 2.0
        maxY = self._ypos + self._height / 2.0

        leftX = self._xpos - self._width / 2.0
        rightX = self._xpos + self._width / 2.0

        # if self._pen:
        #     dc.SetPen(self._pen)
        if self.pen:
            dc.SetPen(wx.Pen(self.pen[0], self.pen[1], wx.SOLID))

        # dc.SetTextForeground(self._textColour)

        # For efficiency, don't do this under X - doesn't make
        # any visible difference for our purposes.
        # if sys.platform[:3] == "win":
        #     dc.SetTextBackground(self._brush.GetColour())

        # if self.GetDisableLabel():
        #     return

        xMargin = 2
        yMargin = 2

        dc.SetBackgroundMode(wx.TRANSPARENT)

        for region in self.GetRegions():
            dc.SetFont(region.GetFont())
            dc.SetTextForeground(region.GetActualColourObject())

            if region._regionProportionY < 0:
                proportion = defaultProportion
            else:
                proportion = region._regionProportionY

            y = currentY + self._height * proportion
            actualY = min(maxY, y)

            centreX = self._xpos
            centreY = currentY + (actualY - currentY) / 2.0

            # print("region._formattedText,", region._formattedText)
            DrawFormattedText(
                dc,
                region._formattedText,
                centreX,
                centreY,
                self._width - 2 * xMargin,
                actualY - currentY - 2 * yMargin,
                region._formatMode,
            )

            if y <= maxY and region != self.GetRegions()[-1]:
                regionPen = region.GetActualPen()
                if regionPen:
                    dc.SetPen(regionPen)
                    dc.DrawLine(int(leftX), int(y), int(rightX), int(y))  # python 3.10 needs ints

            currentY = actualY

    def SetSize(self, w, h, recursive=True):
        """
        Set the size.

        :param `w`: width of rectangle
        :param `h`: heigth of rectangle
        :param `recursive`: not implemented

        """
        self.SetAttachmentSize(w, h)
        self._width = w
        self._height = h
        self.SetRegionSizes()

    def SetRegionSizes(self):
        """
        Set all region sizes according to proportions and this object
        total size.
        """
        if not self.GetRegions():
            return

        if self.GetRegions():
            defaultProportion = 1.0 / len(self.GetRegions())
        else:
            defaultProportion = 0.0
        currentY = self._ypos - self._height / 2.0
        maxY = self._ypos + self._height / 2.0

        for region in self.GetRegions():
            if region._regionProportionY <= 0:
                proportion = defaultProportion
            else:
                proportion = region._regionProportionY

            sizeY = proportion * self._height
            y = currentY + sizeY
            actualY = min(maxY, y)

            centreY = currentY + (actualY - currentY) / 2.0

            region.SetSize(self._width, sizeY)
            region.SetPosition(0, centreY - self._ypos)

            currentY = actualY

    # def GetAttachmentPosition(self, attachment, nth = 0, no_arcs = 1, line = None):
    #     """
    #     Get the attachment position.
    #
    #     Attachment points correspond to regions in the divided box.
    #
    #     :param `attachment`: the attachment ???
    #     :param `nth`: get nth attachment ???
    #     :param `no_arcs`: ???
    #     :param `line`: ???
    #
    #     """
    #     totalNumberAttachments = len(self.GetRegions()) * 2 + 2
    #     if self.GetAttachmentMode() == ATTACHMENT_MODE_NONE or attachment >= totalNumberAttachments:
    #         return Shape.GetAttachmentPosition(self, attachment, nth, no_arcs)
    #
    #     n = len(self.GetRegions())
    #     isEnd = line and line.IsEnd(self)
    #
    #     left = self._xpos - self._width / 2.0
    #     right = self._xpos + self._width / 2.0
    #     top = self._ypos - self._height / 2.0
    #     bottom = self._ypos + self._height / 2.0
    #
    #     # Zero is top, n + 1 is bottom
    #     if attachment == 0:
    #         y = top
    #         if self._spaceAttachments:
    #             if line and line.GetAlignmentType(isEnd) == LINE_ALIGNMENT_TO_NEXT_HANDLE:
    #                 # Align line according to the next handle along
    #                 point = line.GetNextControlPoint(self)
    #                 if point[0] < left:
    #                     x = left
    #                 elif point[0] > right:
    #                     x = right
    #                 else:
    #                     x = point[0]
    #             else:
    #                 x = left + (nth + 1) * self._width / (no_arcs + 1.0)
    #         else:
    #             x = self._xpos
    #     elif attachment == n + 1:
    #         y = bottom
    #         if self._spaceAttachments:
    #             if line and line.GetAlignmentType(isEnd) == LINE_ALIGNMENT_TO_NEXT_HANDLE:
    #                 # Align line according to the next handle along
    #                 point = line.GetNextControlPoint(self)
    #                 if point[0] < left:
    #                     x = left
    #                 elif point[0] > right:
    #                     x = right
    #                 else:
    #                     x = point[0]
    #             else:
    #                 x = left + (nth + 1) * self._width / (no_arcs + 1.0)
    #         else:
    #             x = self._xpos
    #     else: # Left or right
    #         isLeft = not attachment < (n + 1)
    #         if isLeft:
    #             i = totalNumberAttachments - attachment - 1
    #         else:
    #             i = attachment - 1
    #
    #         region = self.GetRegions()[i]
    #         if region:
    #             if isLeft:
    #                 x = left
    #             else:
    #                 x = right
    #
    #             # Calculate top and bottom of region
    #             top = self._ypos + region._y - region._height / 2.0
    #             bottom = self._ypos + region._y + region._height / 2.0
    #
    #             # Assuming we can trust the absolute size and
    #             # position of these regions
    #             if self._spaceAttachments:
    #                 if line and line.GetAlignmentType(isEnd) == LINE_ALIGNMENT_TO_NEXT_HANDLE:
    #                     # Align line according to the next handle along
    #                     point = line.GetNextControlPoint(self)
    #                     if point[1] < bottom:
    #                         y = bottom
    #                     elif point[1] > top:
    #                         y = top
    #                     else:
    #                         y = point[1]
    #                 else:
    #                     y = top + (nth + 1) * region._height / (no_arcs + 1.0)
    #             else:
    #                 y = self._ypos + region._y
    #         else:
    #             return False
    #     return x, y
    #
    # def GetNumberOfAttachments(self):
    #     """
    #     Get the number of attachments.
    #
    #     There are two attachments for each region (left and right),
    #     plus one on the top and one on the bottom.
    #     """
    #     n = len(self.GetRegions()) * 2 + 2
    #
    #     maxN = n - 1
    #     for point in self._attachmentPoints:
    #         if point._id > maxN:
    #             maxN = point._id
    #
    #     return maxN + 1
    #
    # def AttachmentIsValid(self, attachment):
    #     """
    #     Is the attachment valid?
    #
    #     :param `attachment`: the attachment
    #
    #     """
    #     totalNumberAttachments = len(self.GetRegions()) * 2 + 2
    #     if attachment >= totalNumberAttachments:
    #         return Shape.AttachmentIsValid(self, attachment)
    #     else:
    #         return attachment >= 0
    #
    # def MakeControlPoints(self):
    #     """
    #     Make the control points.
    #     """
    #     RectangleShape.MakeControlPoints(self)
    #     self.MakeMandatoryControlPoints()
    #
    # def MakeMandatoryControlPoints(self):
    #     """
    #     Make the mandatory control points.
    #     """
    #     currentY = self.GetY() - self._height / 2.0
    #     maxY = self.GetY() + self._height / 2.0
    #
    #     for i, region in enumerate(self.GetRegions()):
    #         proportion = region._regionProportionY
    #
    #         y = currentY + self._height * proportion
    #         actualY = min(maxY, y)
    #
    #         if region != self.GetRegions()[-1]:
    #             controlPoint = DividedShapeControlPoint(self._canvas, self, i, CONTROL_POINT_SIZE, 0, actualY - self.GetY(), 0)
    #             self._canvas.AddShape(controlPoint)
    #             self._controlPoints.append(controlPoint)
    #
    #         currentY = actualY
    #
    def ResetControlPoints(self):
        """
        Reset the control points.

        :note: May only have the region handles, (n - 1) of them

        """

        if len(self._controlPoints) > len(self.GetRegions()) - 1:
            RectangleShape.ResetControlPoints(self)

        self.ResetMandatoryControlPoints()

    def ResetMandatoryControlPoints(self):
        """
        Reset the mandatory control points.
        """
        currentY = self.GetY() - self._height / 2.0
        maxY = self.GetY() + self._height / 2.0

        i = 0
        for controlPoint in self._controlPoints:
            # NOTE: the original wx.lib.ogl class DividedShapeControlPoint was dropped
            # from wxdiagram; control points no longer carry that type, so update them all.
            if controlPoint is not None:
                region = self.GetRegions()[i]
                proportion = region._regionProportionY

                y = currentY + self._height * proportion
                actualY = min(maxY, y)

                controlPoint._xoffset = 0
                controlPoint._yoffset = actualY - self.GetY()

                currentY = actualY

                i += 1

    #
    # def EditRegions(self):
    #     """
    #     Edit the region colours and styles. Not implemented.
    #     """
    #     print("EditRegions() is unimplemented")
    #
    # def OnRightClick(self, x, y, keys = 0, attachment = 0):
    #     """The right click handler."""
    #     if keys & KEY_CTRL:
    #         self.EditRegions()
    #     else:
    #         RectangleShape.OnRightClick(self, x, y, keys, attachment)


__all__ = ["DividedShape"]
