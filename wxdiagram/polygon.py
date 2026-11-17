import wx

from .core import LinesShape, Shape


class PolygonShape(LinesShape):
    """A closed polygon defined by points offset from its centre."""

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
