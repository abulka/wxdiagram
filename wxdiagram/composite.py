# ---------------------------------------------------------------------------------------------
# Composite shapes for wxdiagram - wraps a number of child shapes into a single sized,
# constrained group that moves as a unit.
#
# Inspired by (and API-compatible with a useful subset of) wx.lib.ogl's composit.py.
#
# A CompositeShape:
#   - is itself a RectangleShape (so it can be selected, resized, saved and loaded)
#   - owns child shapes (AddChild / RemoveChild) which move with it
#   - holds Constraint objects that position children relative to a constraining shape
#   - draws its children recursively
#
# Coordinates: children keep their own absolute x/y coordinates; moving the composite
# moves the children by the same delta.  Bounds are recomputed with CalculateSize()
# and Recompute() (constraint solving) as in wx.lib.ogl, but without needing a wx DC.
# ---------------------------------------------------------------------------------------------

from .core import RectangleShape, Selectable

CONSTRAINT_CENTRED_VERTICALLY = 1
CONSTRAINT_CENTRED_HORIZONTALLY = 2
CONSTRAINT_CENTRED_BOTH = 3
CONSTRAINT_LEFT_OF = 4
CONSTRAINT_RIGHT_OF = 5
CONSTRAINT_ABOVE = 6
CONSTRAINT_BELOW = 7
CONSTRAINT_ALIGNED_TOP = 8
CONSTRAINT_ALIGNED_BOTTOM = 9
CONSTRAINT_ALIGNED_LEFT = 10
CONSTRAINT_ALIGNED_RIGHT = 11

# Like aligned, but with the objects centred on the respective edge of the reference object.
CONSTRAINT_MIDALIGNED_TOP = 12
CONSTRAINT_MIDALIGNED_BOTTOM = 13
CONSTRAINT_MIDALIGNED_LEFT = 14
CONSTRAINT_MIDALIGNED_RIGHT = 15


class ConstraintType:
    """Readable names for the constraint type ids."""

    CONSTRAINT_CENTRED_VERTICALLY = CONSTRAINT_CENTRED_VERTICALLY
    CONSTRAINT_CENTRED_HORIZONTALLY = CONSTRAINT_CENTRED_HORIZONTALLY
    CONSTRAINT_CENTRED_BOTH = CONSTRAINT_CENTRED_BOTH
    CONSTRAINT_LEFT_OF = CONSTRAINT_LEFT_OF
    CONSTRAINT_RIGHT_OF = CONSTRAINT_RIGHT_OF
    CONSTRAINT_ABOVE = CONSTRAINT_ABOVE
    CONSTRAINT_BELOW = CONSTRAINT_BELOW
    CONSTRAINT_ALIGNED_TOP = CONSTRAINT_ALIGNED_TOP
    CONSTRAINT_ALIGNED_BOTTOM = CONSTRAINT_ALIGNED_BOTTOM
    CONSTRAINT_ALIGNED_LEFT = CONSTRAINT_ALIGNED_LEFT
    CONSTRAINT_ALIGNED_RIGHT = CONSTRAINT_ALIGNED_RIGHT
    CONSTRAINT_MIDALIGNED_TOP = CONSTRAINT_MIDALIGNED_TOP
    CONSTRAINT_MIDALIGNED_BOTTOM = CONSTRAINT_MIDALIGNED_BOTTOM
    CONSTRAINT_MIDALIGNED_LEFT = CONSTRAINT_MIDALIGNED_LEFT
    CONSTRAINT_MIDALIGNED_RIGHT = CONSTRAINT_MIDALIGNED_RIGHT


class Constraint:
    """
    Positions one or more constrained shapes relative to a constraining shape.

    :param `type`: one of the CONSTRAINT_* constants
    :param `constraining`: the constraining shape (usually a group or a division)
    :param `constrained`: a list of constrained shapes (or a single shape)
    """

    def __init__(self, theType, constraining, constrained):
        if not isinstance(constrained, list):
            constrained = [constrained]
        self._xSpacing = 0.0
        self._ySpacing = 0.0

        self._constraintType = theType
        self._constrainingObject = constraining

        self._constraintId = 0
        self._constraintName = "noname"

        self._constrainedObjects = constrained[:]

    def __repr__(self):
        return (
            f"<{self.__class__.__module__}.{self.__class__.__name__} type={self._constraintType}>"
        )

    def SetSpacing(self, x, y):
        """Spacing used by ABOVE/BELOW/LEFT_OF/RIGHT_OF constraints (and as a
        fallback when centred objects are larger than the constraining shape)."""
        self._xSpacing = x
        self._ySpacing = y

    @staticmethod
    def Equals(a, b):
        marg = 0.5
        return b <= a + marg and b >= a - marg

    def Evaluate(self):
        """Evaluate the constraint, moving the constrained shapes if needed.

        Returns: True if any object moved, False otherwise.
        """
        x = self._constrainingObject.GetX()
        y = self._constrainingObject.GetY()

        maxWidth, maxHeight = self._constrainingObject.GetBoundingBoxMax()
        minWidth, minHeight = self._constrainingObject.GetBoundingBoxMin()

        if self._constraintType == CONSTRAINT_CENTRED_VERTICALLY:
            n = len(self._constrainedObjects)
            totalObjectHeight = sum(c.GetBoundingBoxMax()[1] for c in self._constrainedObjects)

            if totalObjectHeight + (n + 1) * self._ySpacing <= minHeight:
                spacingY = (minHeight - totalObjectHeight) / (n + 1.0)
                startY = y - minHeight / 2.0
            else:
                spacingY = self._ySpacing
                startY = y - (totalObjectHeight + (n + 1) * spacingY) / 2.0

            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                startY += spacingY + h2 / 2.0
                if not self.Equals(startY, c.GetY()):
                    c.Move(None, c.GetX(), startY, False)
                    changed = True
                startY += h2 / 2.0
            return changed

        if self._constraintType == CONSTRAINT_CENTRED_HORIZONTALLY:
            n = len(self._constrainedObjects)
            totalObjectWidth = sum(c.GetBoundingBoxMax()[0] for c in self._constrainedObjects)

            if totalObjectWidth + (n + 1) * self._xSpacing <= minWidth:
                spacingX = (minWidth - totalObjectWidth) / (n + 1.0)
                startX = x - minWidth / 2.0
            else:
                spacingX = self._xSpacing
                startX = x - (totalObjectWidth + (n + 1) * spacingX) / 2.0

            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                startX += spacingX + w2 / 2.0
                if not self.Equals(startX, c.GetX()):
                    c.Move(None, startX, c.GetY(), False)
                    changed = True
                startX += w2 / 2.0
            return changed

        if self._constraintType == CONSTRAINT_CENTRED_BOTH:
            n = len(self._constrainedObjects)
            totalObjectWidth = sum(c.GetBoundingBoxMax()[0] for c in self._constrainedObjects)
            totalObjectHeight = sum(c.GetBoundingBoxMax()[1] for c in self._constrainedObjects)

            if totalObjectWidth + (n + 1) * self._xSpacing <= minWidth:
                spacingX = (minWidth - totalObjectWidth) / (n + 1.0)
                startX = x - minWidth / 2.0
            else:
                spacingX = self._xSpacing
                startX = x - (totalObjectWidth + (n + 1) * spacingX) / 2.0

            if totalObjectHeight + (n + 1) * self._ySpacing <= minHeight:
                spacingY = (minHeight - totalObjectHeight) / (n + 1.0)
                startY = y - minHeight / 2.0
            else:
                spacingY = self._ySpacing
                startY = y - (totalObjectHeight + (n + 1) * spacingY) / 2.0

            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                startX += spacingX + w2 / 2.0
                startY += spacingY + h2 / 2.0
                if not self.Equals(startX, c.GetX()) or not self.Equals(startY, c.GetY()):
                    c.Move(None, startX, startY, False)
                    changed = True
                startX += w2 / 2.0
                startY += h2 / 2.0
            return changed

        if self._constraintType == CONSTRAINT_LEFT_OF:
            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                x3 = x - minWidth / 2.0 - w2 / 2.0 - self._xSpacing
                if not self.Equals(x3, c.GetX()):
                    c.Move(None, x3, c.GetY(), False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_RIGHT_OF:
            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                x3 = x + minWidth / 2.0 + w2 / 2.0 + self._xSpacing
                if not self.Equals(x3, c.GetX()):
                    c.Move(None, x3, c.GetY(), False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_ABOVE:
            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                y3 = y - minHeight / 2.0 - h2 / 2.0 - self._ySpacing
                if not self.Equals(y3, c.GetY()):
                    c.Move(None, c.GetX(), y3, False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_BELOW:
            changed = False
            for c in self._constrainedObjects:
                w2, h2 = c.GetBoundingBoxMax()
                y3 = y + minHeight / 2.0 + h2 / 2.0 + self._ySpacing
                if not self.Equals(y3, c.GetY()):
                    c.Move(None, c.GetX(), y3, False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_ALIGNED_TOP:
            changed = False
            for c in self._constrainedObjects:
                h2 = c.GetBoundingBoxMax()[1]
                target = y - minHeight / 2.0 + h2 / 2.0
                if abs(target - c.GetY()) > 0.5:
                    c.Move(None, c.GetX(), target, False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_ALIGNED_BOTTOM:
            changed = False
            for c in self._constrainedObjects:
                h2 = c.GetBoundingBoxMax()[1]
                target = y + minHeight / 2.0 - h2 / 2.0
                if abs(target - c.GetY()) > 0.5:
                    c.Move(None, c.GetX(), target, False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_ALIGNED_LEFT:
            changed = False
            for c in self._constrainedObjects:
                w2 = c.GetBoundingBoxMax()[0]
                target = x - minWidth / 2.0 + w2 / 2.0
                if abs(target - c.GetX()) > 0.5:
                    c.Move(None, target, c.GetY(), False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_ALIGNED_RIGHT:
            changed = False
            for c in self._constrainedObjects:
                w2 = c.GetBoundingBoxMax()[0]
                target = x + minWidth / 2.0 - w2 / 2.0
                if abs(target - c.GetX()) > 0.5:
                    c.Move(None, target, c.GetY(), False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_MIDALIGNED_TOP:
            changed = False
            for c in self._constrainedObjects:
                target = y - minHeight / 2.0
                if not self.Equals(target, c.GetY()):
                    c.Move(None, c.GetX(), target, False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_MIDALIGNED_BOTTOM:
            changed = False
            for c in self._constrainedObjects:
                target = y + minHeight / 2.0
                if not self.Equals(target, c.GetY()):
                    c.Move(None, c.GetX(), target, False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_MIDALIGNED_LEFT:
            changed = False
            for c in self._constrainedObjects:
                target = x - minWidth / 2.0
                if not self.Equals(target, c.GetX()):
                    c.Move(None, target, c.GetY(), False)
                    changed = True
            return changed

        if self._constraintType == CONSTRAINT_MIDALIGNED_RIGHT:
            changed = False
            for c in self._constrainedObjects:
                target = x + minWidth / 2.0
                if not self.Equals(target, c.GetX()):
                    c.Move(None, target, c.GetY(), False)
                    changed = True
            return changed

        # Constraint types we don't handle are ignored.
        return False


class CompositeShape(RectangleShape, Selectable):
    """A rectangle whose child shapes move with it, optionally constrained in layout."""

    def __init__(self):
        RectangleShape.__init__(self, 100, 100, 300, 300)
        self._compositeChildren = []
        self._constraints = []

    # -- child management -------------------------------------------------------------------

    def AddChild(self, child, addAfter=None):
        if addAfter is not None:
            self._compositeChildren.insert(self._compositeChildren.index(addAfter) + 1, child)
        else:
            self._compositeChildren.append(child)
        child.SetParent(self)
        if self.GetCanvas():
            child.SetCanvas(self.GetCanvas())
        return child

    # alias used by the persistence loader
    add_child = AddChild

    def RemoveChild(self, child):
        if child in self._compositeChildren:
            self._compositeChildren.remove(child)
        self.RemoveChildFromConstraints(child)
        child.SetParent(None)
        return child

    def GetChildren(self):
        return self._compositeChildren

    def GetConstraints(self):
        """Return the constraints owned by this composite."""
        return self._constraints

    def GetParent(self):
        return self._parent

    def SetParent(self, p):
        self._parent = p

    def GetTopAncestor(self):
        if self.GetParent():
            return self.GetParent().GetTopAncestor()
        return self

    # -- canvas ----------------------------------------------------------------------------

    def SetCanvas(self, canvas):
        super().SetCanvas(canvas)
        for child in self._compositeChildren:
            child.SetCanvas(canvas)

    # -- geometry ----------------------------------------------------------------------------

    def move(self, x, y):
        for child in self._compositeChildren:
            child.move(x, y)
            if hasattr(child, "MoveLinks"):
                child.MoveLinks(None)
        super().move(x, y)

    def move_to(self, x, y):
        delta_x = x - self.x[0]
        delta_y = y - self.y[0]
        self.move(delta_x, delta_y)

    def CalculateSize(self):
        """Resize and reposition the composite to enclose its children."""
        minX = 9999999.9
        minY = 9999999.9
        maxX = -9999999.9
        maxY = -9999999.9
        if not self._compositeChildren:
            return

        for child in self._compositeChildren:
            if isinstance(child, CompositeShape):
                child.CalculateSize()
            w, h = child.GetBoundingBoxMax()
            minX = min(minX, child.GetX() - w / 2.0)
            maxX = max(maxX, child.GetX() + w / 2.0)
            minY = min(minY, child.GetY() - h / 2.0)
            maxY = max(maxY, child.GetY() + h / 2.0)

        self.x = [minX, maxX]
        self.y = [minY, maxY]

    def moveto(self, x, y):  # absolute move convenience
        delta_x = x - self.GetX()
        delta_y = y - self.GetY()
        self.move(delta_x, delta_y)

    # -- constraints ---------------------------------------------------------------------

    def AddConstraint(self, constraint):
        self._constraints.append(constraint)
        if constraint._constraintId == 0:
            import wx

            constraint._constraintId = wx.NewIdRef()
        return constraint

    def AddSimpleConstraint(self, theType, constraining, constrained):
        constraint = Constraint(theType, constraining, constrained)
        self._constraints.append(constraint)
        return constraint

    def FindConstraint(self, cId):
        for constraint in self._constraints:
            if constraint._constraintId == cId:
                return constraint, self
        for child in self._compositeChildren:
            if isinstance(child, CompositeShape):
                found = child.FindConstraint(cId)
                if found:
                    return found[0], found[1]
        return None

    def DeleteConstraint(self, constraint):
        if constraint in self._constraints:
            self._constraints.remove(constraint)

    def RemoveChildFromConstraints(self, child):
        """Remove ``child`` from any constraint that references it.

        A constraint whose constraining object is the child is removed
        entirely; otherwise the child is removed from the constrained list.
        Empty constraints are dropped.
        """
        for constraint in list(self._constraints):
            if constraint._constrainingObject is child:
                self._constraints.remove(constraint)
                continue
            if child in constraint._constrainedObjects:
                constraint._constrainedObjects = [
                    obj for obj in constraint._constrainedObjects if obj is not child
                ]
                if not constraint._constrainedObjects:
                    self._constraints.remove(constraint)

        for nested in self._compositeChildren:
            if isinstance(nested, CompositeShape):
                nested.RemoveChildFromConstraints(child)

    def DeleteConstraintsInvolvingChild(self, child):
        """Alias for :meth:`RemoveChildFromConstraints`."""
        self.RemoveChildFromConstraints(child)

    def Constrain(self):
        """Evaluate the constraints once. Returns True if anything moved."""
        self.CalculateSize()
        changed = False
        for child in self._compositeChildren:
            if isinstance(child, CompositeShape) and child.Constrain():
                changed = True
        for constraint in self._constraints:
            if constraint.Evaluate():
                changed = True
        return changed

    def Recompute(self, maxIterations=500):
        """Evaluate constraints until stable (or maxIterations is reached).

        Returns True if the constraints settled, False if it gave up.
        """
        for _ in range(maxIterations):
            if not self.Constrain():
                return True
        return False

    # -- drawing ----------------------------------------------------------------------------

    def draw(self, dc):
        RectangleShape.draw(self, dc)
        for child in self._compositeChildren:
            child.draw(dc)

    def HitTest(self, x, y):
        return self.x[0] <= x <= self.x[1] and self.y[0] <= y <= self.y[1]

    # -- persistence -------------------------------------------------------------------------

    def serialize_constraints(self, id_map):
        out = []
        for c in self._constraints:
            out.append(
                {
                    "type": c._constraintType,
                    "constraining": id_map.get(id(c._constrainingObject)),
                    "constrained": [id_map.get(id(o)) for o in c._constrainedObjects],
                    "xSpacing": c._xSpacing,
                    "ySpacing": c._ySpacing,
                    "id": c._constraintId,
                }
            )
        return out

    def deserialize_constraints(self, data, id_to_shape):
        for entry in data:
            constraining = id_to_shape.get(entry.get("constraining"))
            constrained = [id_to_shape.get(i) for i in entry.get("constrained", [])]
            constrained = [c for c in constrained if c is not None]
            if constraining is None or not constrained:
                continue
            constraint = Constraint(entry["type"], constraining, constrained)
            constraint.SetSpacing(entry.get("xSpacing", 0.0), entry.get("ySpacing", 0.0))
            constraint._constraintId = entry.get("id", 0)
            self._constraints.append(constraint)


__all__ = [
    "ConstraintType",
    "Constraint",
    "CompositeShape",
    "CONSTRAINT_CENTRED_VERTICALLY",
    "CONSTRAINT_CENTRED_HORIZONTALLY",
    "CONSTRAINT_CENTRED_BOTH",
    "CONSTRAINT_LEFT_OF",
    "CONSTRAINT_RIGHT_OF",
    "CONSTRAINT_ABOVE",
    "CONSTRAINT_BELOW",
    "CONSTRAINT_ALIGNED_TOP",
    "CONSTRAINT_ALIGNED_BOTTOM",
    "CONSTRAINT_ALIGNED_LEFT",
    "CONSTRAINT_ALIGNED_RIGHT",
    "CONSTRAINT_MIDALIGNED_TOP",
    "CONSTRAINT_MIDALIGNED_BOTTOM",
    "CONSTRAINT_MIDALIGNED_LEFT",
    "CONSTRAINT_MIDALIGNED_RIGHT",
]
