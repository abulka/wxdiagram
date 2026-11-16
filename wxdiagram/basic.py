# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         basic.py
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
The basic shapes for OGL
"""

import wx

from .geometry import FORMAT_CENTRE_HORIZ, FORMAT_CENTRE_VERT


# Default pens/brushes/font.  wx objects cannot be created before the wx.App,
# so use these accessors.  Module-level names are kept for backwards
# compatibility (they start as None and get set by initialize()).
WhiteBackgroundPen = None
WhiteBackgroundBrush = None
TransparentPen = None
BlackForegroundPen = None
NormalFont = None


def _ensure_defaults():
    global WhiteBackgroundPen, WhiteBackgroundBrush, TransparentPen
    global BlackForegroundPen, NormalFont

    if WhiteBackgroundPen is None:
        WhiteBackgroundPen = wx.Pen(wx.WHITE, 1, wx.PENSTYLE_SOLID)
    if WhiteBackgroundBrush is None:
        WhiteBackgroundBrush = wx.Brush(wx.WHITE, wx.BRUSHSTYLE_SOLID)
    if TransparentPen is None:
        TransparentPen = wx.Pen(wx.WHITE, 1, wx.PENSTYLE_TRANSPARENT)
    if BlackForegroundPen is None:
        BlackForegroundPen = wx.Pen(wx.BLACK, 1, wx.PENSTYLE_SOLID)
    if NormalFont is None:
        # ANDY changed to 14, was 10
        NormalFont = wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)


def get_white_background_pen():
    _ensure_defaults()
    return WhiteBackgroundPen


def get_white_background_brush():
    _ensure_defaults()
    return WhiteBackgroundBrush


def get_black_foreground_pen():
    _ensure_defaults()
    return BlackForegroundPen


def get_transparent_pen():
    _ensure_defaults()
    return TransparentPen


def get_normal_font():
    _ensure_defaults()
    return NormalFont


def initialize():
    """Initialize OGL.

    Kept for backwards compatibility with code that calls initialize()
    after the app object has been created.  Not strictly required anymore: the
    library creates these objects lazily on first use.
    """
    _ensure_defaults()


class ShapeTextLine(object):
    """The :class:`ShapeTextLine` class."""

    def __init__(self, the_x, the_y, the_line):
        """
        Default class constructor.

        :param int `the_x`: the x position
        :param int `the_y`: the y position
        :param str `the_line`: the text

        """
        self._x = the_x
        self._y = the_y
        self._line = the_line

    def GetX(self):
        """Get the x position."""
        return self._x

    def GetY(self):
        """Get the y position."""
        return self._y

    def SetX(self, x):
        """
        Set the x position.

        :param int `x`: the x position

        """
        self._x = x

    def SetY(self, y):
        """
        Set the y position.

        :param int `y`: the x position

        """
        self._y = y

    def SetText(self, text):
        """
        Set the text.

        :param str `text`: the text

        """
        self._line = text

    def GetText(self):
        """Get the text."""
        return self._line


class ShapeRegion(object):
    """The :class:`ShapeRegion` class."""

    def __init__(self, region=None):
        """
        Default class constructor

        :param `region`: a parent region or None???

        """
        if region:
            self._regionText = region._regionText
            self._regionName = region._regionName
            self._textColour = region._textColour

            self._font = region._font
            self._minHeight = region._minHeight
            self._minWidth = region._minWidth
            self._width = region._width
            self._height = region._height
            self._x = region._x
            self._y = region._y

            self._regionProportionX = region._regionProportionX
            self._regionProportionY = region._regionProportionY
            self._formatMode = region._formatMode
            self._actualColourObject = region._actualColourObject
            self._actualPenObject = None
            self._penStyle = region._penStyle
            self._penColour = region._penColour

            self.ClearText()
            for line in region._formattedText:
                new_line = ShapeTextLine(line.GetX(), line.GetY(), line.GetText())
                self._formattedText.append(new_line)
        else:
            self._regionText = ""
            self._font = get_normal_font()
            self._minHeight = 5.0
            self._minWidth = 5.0
            self._width = 0.0
            self._height = 0.0
            self._x = 0.0
            self._y = 0.0

            self._regionProportionX = -1.0
            self._regionProportionY = -1.0
            self._formatMode = FORMAT_CENTRE_HORIZ | FORMAT_CENTRE_VERT
            self._regionName = ""
            self._textColour = "BLACK"
            self._penColour = "BLACK"
            self._penStyle = wx.PENSTYLE_SOLID
            self._actualColourObject = wx.TheColourDatabase.Find("BLACK")
            self._actualPenObject = None

            self._formattedText = []

    def ClearText(self):
        """Clear the text."""
        self._formattedText = []

    def SetFont(self, f):
        """
        Set the font.

        :param `f`: an instance of :class:`wx.Font`
        """
        self._font = f

    def SetMinSize(self, w, h):
        """
        Set the minumum size.

        :param `w`: the minimum width
        :Param `h`: the minimum height

        """
        self._minWidth = w
        self._minHeight = h

    def SetSize(self, w, h):
        """
        Set the size.

        :param `w`: the width
        :Param `h`: the jeight

        """
        self._width = w
        self._height = h

    def SetPosition(self, xp, yp):
        """
        Set the position.

        :param `xp`: the x position
        :Param `yp`: the y position

        """
        self._x = xp
        self._y = yp

    def SetProportions(self, xp, yp):
        """
        Set the proportions.

        :param `xp`: the x region proportion
        :Param `yp`: the y region proportion

        """
        self._regionProportionX = xp
        self._regionProportionY = yp

    def SetFormatMode(self, mode):
        """
        Set the format mode of the region.

        :param `mode`: can be a bit list of the following

        ============================== ==============================
        Format mode                    Description
        ============================== ==============================
        `FORMAT_NONE`                  No formatting
        `FORMAT_CENTRE_HORIZ`          Horizontal centring
        `FORMAT_CENTRE_VERT`           Vertical centring
        ============================== ==============================

        """
        self._formatMode = mode

    def SetColour(self, col):
        """
        Set the colour.

        :param str `col`: a valid colour name,
         see :class:`wx.ColourDatabase`

        """
        self._textColour = col
        self._actualColourObject = col

    def GetActualColourObject(self):
        """Get the actual colour object from the :class:`wx.ColourDatabase`."""
        self._actualColourObject = wx.TheColourDatabase.Find(self.GetColour())
        return self._actualColourObject

    def SetPenColour(self, col):
        """
        Set the pen colour.

        :param str `col`: a valid colour name,
         see :class:`wx.ColourDatabase`

        """
        self._penColour = col
        self._actualPenObject = None

    def GetActualPen(self):
        """
        Get actual pen.

        :note: Returns NULL if the pen is invisible
         (different to pen being transparent; indicates that
         region boundary should not be drawn.)

        """
        if self._actualPenObject:
            return self._actualPenObject

        if not self._penColour:
            return None
        if self._penColour == "Invisible":
            return None
        self._actualPenObject = wx.Pen(self._penColour, 1, self._penStyle)
        return self._actualPenObject

    def SetText(self, s):
        """
        Set the text.

        :param str `s`: the text

        """
        self._regionText = s

    def SetName(self, s):
        """
        Set the name.

        :param str `s`: the name

        """
        self._regionName = s

    def GetText(self):
        """Get the text."""
        return self._regionText

    def GetFont(self):
        """Get the font."""
        return self._font

    def GetMinSize(self):
        """Get the minimum size."""
        return self._minWidth, self._minHeight

    def GetProportion(self):
        """Get the proportion."""
        return self._regionProportionX, self._regionProportionY

    def GetSize(self):
        """Get the size."""
        return self._width, self._height

    def GetPosition(self):
        """Get the position."""
        return self._x, self._y

    def GetFormatMode(self):
        """Get the format mode."""
        return self._formatMode

    def GetName(self):
        """Get the name."""
        return self._regionName

    def GetColour(self):
        """Get the colour."""
        return self._textColour

    def GetFormattedText(self):
        """Get the formatted text."""
        return self._formattedText

    def GetPenColour(self):
        """Get the pen colour"""
        return self._penColour

    def GetPenStyle(self):
        """Get the pen style."""
        return self._penStyle

    def SetPenStyle(self, style):
        """
        Set the pen style.

        :param `style`: the style, see :class:`wx.Pen`

        """
        self._penStyle = style
        self._actualPenObject = None

    def GetWidth(self):
        """Get the width."""
        return self._width

    def GetHeight(self):
        """Get the height."""
        return self._height


__all__ = [
    "initialize",
    "ShapeTextLine",
    "ShapeRegion",
    "get_white_background_pen",
    "get_white_background_brush",
    "get_black_foreground_pen",
    "get_transparent_pen",
    "get_normal_font",
    "WhiteBackgroundPen",
    "WhiteBackgroundBrush",
    "TransparentPen",
    "BlackForegroundPen",
    "NormalFont",
]
