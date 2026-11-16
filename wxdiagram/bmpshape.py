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

from .core import RectangleShape, Selectable, Resizeable


class BitmapShape(RectangleShape, Selectable, Resizeable):  # ANDY
    """The :class:`wx.BitmapShape` class draws a bitmap (non-resizable)."""

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


__all__ = ["BitmapShape"]
