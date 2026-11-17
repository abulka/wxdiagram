# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         bmpshape.py
# Purpose:      The basic OGL shapes
#
# Author:       Pierre Hjälm (from C++ original by Julian Smart)
#               Andy Bulka - portions extracted, altered or deleted to suit ogllike and pynsource
#
# Created:      2004-05-08
# Copyright:    (c) 2004 Pierre Hjälm - 1998 Julian Smart
# Licence:      wxWindows license
# Tags:         phoenix-port, unittest, py3-port, documented
# ----------------------------------------------------------------------------

"""
The :class:`~lib.ogl.bmpshape.BitmapShape` class.
"""

import wx

from .core import RectangleShape, Selectable, Resizeable, resize_rect_from_handle


class BitmapShape(RectangleShape, Selectable, Resizeable):  # ANDY
    """The :class:`wx.BitmapShape` class draws a bitmap (non-resizable)."""

    is_bitmap = True

    def __init__(self):
        """
        Default class constructor.
        """
        # RectangleShape.__init__(self, 100, 50)  - wx ogl is width based
        RectangleShape.__init__(self, 0, 50, 0, 50)  # ogllike is x,y,x2,y2 based
        Resizeable.__init__(self)  # ANDY
        Selectable.__init__(self)  # ANDY
        self._filename = ""

    # def OnDraw(self, dc):
    def draw(self, dc):
        """The draw handler."""
        if not self._bitmap.IsOk():
            return

        x = self._xpos - self._bitmap.GetWidth() / 2.0
        y = self._ypos - self._bitmap.GetHeight() / 2.0
        dc.DrawBitmap(self._bitmap, int(x), int(y), True)  # python 3.10 needs ints

    def SetSize(self, w, h, recursive=True):
        """
        Set the size.

        :param `w`: the width
        :param `h`: the heigth
        :param `recursive`: not used

        """

        if self._bitmap.IsOk():
            w = self._bitmap.GetWidth()
            h = self._bitmap.GetHeight()

        self.SetAttachmentSize(w, h)

        self._width = w
        self._height = h

        self.SetDefaultRegionSize()

    def GetBitmap(self):
        """Get the associated bitmap."""
        return self._bitmap

    def SetBitmap(self, bitmap):
        """Set the associated bitmap.

        :param `bitmap`: a :class:`wx.Bitmap` instance

        :note: You can delete the bitmap from the calling application, since
         reference counting will take care of holding on to the internal bitmap
         data.

        """
        self._bitmap = bitmap
        if self._bitmap.IsOk():
            self.SetSize(self._bitmap.GetWidth(), self._bitmap.GetHeight())

    def SetFilename(self, f):
        """Set the bitmap filename.

        :param str `f`: the bitmap file name

        """
        self._filename = f

    def GetFilename(self):
        """Return the bitmap filename."""
        return self._filename


class ResizableBitmapShape(BitmapShape):
    """A bitmap shape whose displayed bitmap is rescaled when it is resized."""

    def __init__(self):
        BitmapShape.__init__(self)
        self._ori_bmp = None

    def ResetSize(self):
        """Restore the bitmap's original dimensions."""
        if self._bitmap.IsOk():
            self.SetSize(self._ori_bmp.GetWidth(), self._ori_bmp.GetHeight())

    def SetSize(self, w, h, recursive=True):
        w = max(1.0, float(w))
        h = max(1.0, float(h))
        # Keep the geometry authoritative; draw() stretches the original bitmap
        # in one blit.  Rescaling the bitmap on every mouse-move was slow and
        # made the image lag behind the cursor.
        #
        # Keep the geometry in floats.  Rounding to whole units here loses the
        # fractional part of every drag delta, which makes the image fall
        # further behind the mouse at non-integer zoom levels.
        self.SetAttachmentSize(w, h)
        self.x = [self.x[0], self.x[0] + w]
        self.y = [self.y[0], self.y[0] + h]
        self.SetDefaultRegionSize()

    def draw(self, dc):
        if not self._ori_bmp or not self._ori_bmp.IsOk():
            return
        x1, y1 = int(round(self.x[0])), int(round(self.y[0]))
        width = max(1, int(round(self.x[1])) - x1)
        height = max(1, int(round(self.y[1])) - y1)
        source = wx.MemoryDC(self._ori_bmp)
        try:
            dc.StretchBlit(
                x1,
                y1,
                width,
                height,
                source,
                0,
                0,
                self._ori_bmp.GetWidth(),
                self._ori_bmp.GetHeight(),
            )
        finally:
            source.SelectObject(wx.NullBitmap)

    def SetBitmap(self, bitmap):
        BitmapShape.SetBitmap(self, bitmap)
        self._ori_bmp = bitmap

    def move_handle(self, index, dx, dy, free_aspect=False):
        """Resize from a drag handle, keeping the opposite corner fixed.

        Only the dragged point moves: changing the size and then re-deriving
        the far edge (as ``SetSize`` does) would re-anchor the shape at its
        top-left and quantise the drag, so the image lags behind the mouse.
        The resize is proportional unless ``free_aspect`` is set.
        """
        resize_rect_from_handle(self, index, dx, dy, free_aspect)
        return True


__all__ = ["BitmapShape", "ResizableBitmapShape"]
