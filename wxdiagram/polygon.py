import wx

from .core import LinesShape, Shape


class PolygonShape(LinesShape):
    """A closed polygon defined by points offset from its centre."""

    #: resize from the bounding box, not one vertex at a time
    uses_bounding_box_handles = True

    def __init__(self):
        """The ogl-like version expects points to be added later via Create()."""
        super().__init__([])

    def Create(self, the_points=None):
        """Set the polygon points from a list of ``(x, y)`` tuples."""
        self.ClearPoints()
        for point in the_points:
            self.x.append(point[0])
            self.y.append(point[1])

    def ClearPoints(self):
        """Clear the points."""
        self.x = []
        self.y = []

    def HitTest(self, x, y):
        """Interior hit test (ray casting), so the whole polygon is clickable."""
        points = list(zip(self.x, self.y))
        if len(points) < 3:
            return False
        inside = False
        previous_x, previous_y = points[-1]
        for current_x, current_y in points:
            if (current_y > y) != (previous_y > y):
                crossing_x = (previous_x - current_x) * (y - current_y)
                crossing_x = crossing_x / (previous_y - current_y) + current_x
                if x < crossing_x:
                    inside = not inside
            previous_x, previous_y = current_x, current_y
        return inside

    def GetBoundingBoxMin(self):
        """Return ``(width, height)`` of the vertex bounding box."""
        if not self.x or not self.y:
            return 0, 0
        return abs(max(self.x) - min(self.x)), abs(max(self.y) - min(self.y))

    def GetX(self):
        """Return the x position of the bbox centre."""
        if not self.x:
            return 0
        return (min(self.x) + max(self.x)) / 2.0

    def GetY(self):
        """Return the y position of the bbox centre."""
        if not self.y:
            return 0
        return (min(self.y) + max(self.y)) / 2.0

    def GetPerimeterPoint(self, x1, y1, x2, y2):
        """Clip the ``centre -> target`` ray to the polygon's edges."""
        if len(self.x) < 3 or len(self.y) < 3:
            return self.GetX(), self.GetY()
        cx, cy = self.GetX(), self.GetY()
        dx = x2 - cx
        dy = y2 - cy
        if dx == 0 and dy == 0:
            return cx, cy
        best_t = None
        points = list(zip(self.x, self.y))
        for index, (ax, ay) in enumerate(points):
            bx, by = points[(index + 1) % len(points)]
            ex = bx - ax
            ey = by - ay
            denom = dx * ey - dy * ex
            if abs(denom) < 1e-12:
                continue
            acx = ax - cx
            acy = ay - cy
            t = (acx * ey - acy * ex) / denom
            u = (acx * dy - acy * dx) / denom
            if t < 0.0 or u < 0.0 or u > 1.0:
                continue
            if best_t is None or t < best_t:
                best_t = t
        if best_t is None:
            return cx, cy
        return cx + dx * best_t, cy + dy * best_t

    def move_handle(self, index, dx, dy, free_aspect=False, from_center=False):
        """Scale all vertices from the bounding box.

        ``index`` selects a corner/edge handle using the same layout as
        rectangles (see ``RECT_HANDLES``); the opposite side stays fixed
        unless ``from_center`` is set.  Corner drags stay proportional unless
        ``free_aspect`` is set.  Returns True (handled).
        """
        from .core import RECT_HANDLES

        if not self.x or not self.y:
            return False
        min_x, max_x = min(self.x), max(self.x)
        min_y, max_y = min(self.y), max(self.y)
        old_width = max_x - min_x
        old_height = max_y - min_y
        if old_width <= 0 or old_height <= 0:
            return False
        xi, yi = RECT_HANDLES[index] if 0 <= index < len(RECT_HANDLES) else (1, 1)
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        width, height = old_width, old_height
        factor = 2.0 if from_center else 1.0
        if xi is not None:
            sign = 1.0 if xi == 1 else -1.0
            width = max(1.0, old_width + sign * dx * factor)
        if yi is not None:
            sign = 1.0 if yi == 1 else -1.0
            height = max(1.0, old_height + sign * dy * factor)
        if not free_aspect and xi is not None and yi is not None:
            ratio = old_width / old_height
            if abs(width - old_width) >= abs(height - old_height):
                height = max(1.0, width / ratio)
            else:
                width = max(1.0, height * ratio)
        if from_center:
            new_x0 = center_x - width / 2.0
            new_y0 = center_y - height / 2.0
        else:
            if xi is None:
                new_x0 = min_x
                width = old_width
            elif xi == 0:
                new_x0 = max_x - width
            else:
                new_x0 = min_x
            if yi is None:
                new_y0 = min_y
                height = old_height
            elif yi == 0:
                new_y0 = max_y - height
            else:
                new_y0 = min_y
        scale_x = width / old_width if old_width else 1.0
        scale_y = height / old_height if old_height else 1.0
        self.x = [new_x0 + (value - min_x) * scale_x for value in self.x]
        self.y = [new_y0 + (value - min_y) * scale_y for value in self.y]
        return True

    def draw(self, dc):
        """Draw a closed polygon.

        ``LinesShape.draw`` draws an open polyline, so the last edge back to
        the first point would be missing.
        """
        Shape.draw(self, dc)
        if len(self.x) < 2 or len(self.y) < 2:
            return
        points = [wx.Point(int(x), int(y)) for x, y in zip(self.x, self.y)]
        dc.DrawPolygon(points)


__all__ = ["PolygonShape"]
