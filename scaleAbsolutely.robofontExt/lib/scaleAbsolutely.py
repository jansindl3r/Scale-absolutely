import math

from pathlib import Path
from functools import wraps
from typing import Callable, Union, List, Tuple

from mojo.events import addObserver, clearObservers
from mojo.extensions import getExtensionDefault, setExtensionDefault
from lib.UI.roundRectButton import RoundRectButton
from lib.UI.inspector.transformPane import TransformPane
from vanilla import Button, CheckBox
from lib.UI.integerEditText import IntegerEditText, NumberEditText


extensionKey = "jan-sindler.scale.absolutely"
key_scaleX_percentage = "jan-sindler.scale.absolutely.x.perc"
key_scaleX_points = "jan-sindler.scale.absolutely.x.points"
key_scaleY_percentage = "jan-sindler.scale.absolutely.y.perc"
key_scaleY_points = "jan-sindler.scale.absolutely.y.points"


def possibleZeroDivison(numr, dnom, result=1) -> Union[float, int]:
    """
    it is expected that zero divison can appear. Like when scaling
    a path that has width but no height
    """
    if not numr:
        # if numr == zero or None
        return result
    try:
        # probably unnecessary, with the new if statement
        return numr / dnom
    except ZeroDivisionError:
        return result


def getBounds(glyph) -> Tuple[int, float]:
    pointObjects = glyph.selection
    if not pointObjects:
        container: list = []
        for contour in glyph:
            for segment in contour:
                for point in segment:
                    if point.type.lower() != "offcurve":
                        container.append(point)
        pointObjects = container
    points = tuple(pt.position for pt in pointObjects)
    xMin, _ = min(points, key=lambda x: x[0])
    xMax, _ = max(points, key=lambda x: x[0])
    _, yMin = min(points, key=lambda x: x[1])
    _, yMax = max(points, key=lambda x: x[1])

    return xMax - xMin, yMax - yMin


def absoluteScaleCallback(self, sender) -> None:
    """
    Absolute point scale callback. It uses the original one,
    But it recalculates the scale based on wanted point width, height.
    """

    curWidth, curHeight = getBounds(CurrentGlyph())
    valueX = self.scaleX.get()
    valueY = self.scaleY.get()
    setExtensionDefault(key_scaleX_points, valueX)
    setExtensionDefault(key_scaleY_points, valueY)

    _scaleX = possibleZeroDivison(valueX, curWidth)
    _scaleY = possibleZeroDivison(valueY, curHeight)

    transformDict = dict(scaleX=_scaleX * 100, scaleY=_scaleY * 100)
    self._callculateTransformation(transformDict, self.glyph)
    self._transformMatrixToDefaults()
    self._setUndoManagerForGlyphs([self.glyph], isinstance(sender, Button))


def absoluteDecorator(func: Callable, otherFunc: Callable) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> None:
        def newFunc(self, *args, **kwargs) -> None:
            if getExtensionDefault(extensionKey):
                otherFunc(self, *args, **kwargs)
            else:
                func(self, *args, **kwargs)
            return None

        return newFunc(self, *args, **kwargs)

    return wrapper


setattr(
    TransformPane,
    "scaleCallback",
    absoluteDecorator(TransformPane.scaleCallback, absoluteScaleCallback),
)


class ScaleAbsolutely:
    def __init__(self, extensionKey: str) -> None:
        addObserver(
            self,
            "inspectorWindowWillShowDescriptions",
            "inspectorWindowWillShowDescriptions",
        )
        self.extensionKey = extensionKey
        self.stateDict = {True: "pt", False: "%"}

    def setSign(self, state: bool) -> None:
        """
        Scale tab - change % and pt, depending on its state
        """
        sign = self.stateDict[state]
        self.view.scaleYProcent.set(sign)
        self.view.scaleXProcent.set(sign)

    def absoluteCheckBoxCallback(self, sender) -> None:
        """
        switching state of button globally and notation of input fields
        """
        curValueX, curValueY = self.view.scaleX.get(), self.view.scaleY.get()
        if sender.get():
            # points
            state = True
            setExtensionDefault(key_scaleX_percentage, curValueX)
            setExtensionDefault(key_scaleY_percentage, curValueY)
            valueX = getExtensionDefault(key_scaleX_points, fallback=100)
            valueY = getExtensionDefault(key_scaleY_points, fallback=100)

        else:
            setExtensionDefault(key_scaleX_points, curValueX)
            setExtensionDefault(key_scaleY_points, curValueY)
            valueX = getExtensionDefault(key_scaleX_percentage, fallback=100)
            valueY = getExtensionDefault(key_scaleY_percentage, fallback=100)
            state = False

        self.view.scaleX.originalSet(valueX if valueX else "")
        self.view.scaleY.originalSet(valueY if valueY else "")
        setExtensionDefault(self.extensionKey, state)
        self.setSign(state)

    def setInput(self, value: str, *args, **kwargs) -> None:
        """
        sets input's text in points. F.e. when scaling
        """
        if len(value):
            curWidth, curHeight = list(map(round, getBounds(CurrentGlyph())))
            self.view.scaleX.originalSet(curWidth)
            self.view.scaleY.originalSet(curHeight)
        return None

    def inspectorWindowWillShowDescriptions(self, notification) -> None:
        """
        sets the new checkbox and moves the other a bit away
        """
        for subMenu in notification["descriptions"]:
            if subMenu["label"] == "Transform":
                view = subMenu["view"]
                break
        if view:
            state = getExtensionDefault(self.extensionKey, fallback=False)
            left, top, width, height = view.scaleProportional.getPosSize()
            view.scaleProportional.setPosSize(
                (left, math.ceil(top - height / 2) + 2, width, height)
            )
            scaleAbsolutelyCheckBox = CheckBox(
                (left, math.floor(top + height / 2), width, height),
                "pt",
                sizeStyle="small",
                callback=(self.absoluteCheckBoxCallback),
                value=state,
            )
            view.scaleAbsolutelyCheckBox = scaleAbsolutelyCheckBox
            self.view = view

            setattr(self.view.scaleX, "originalSet", self.view.scaleX.set)
            setattr(self.view.scaleY, "originalSet", self.view.scaleY.set)
            setattr(
                self.view.scaleX,
                "set",
                absoluteDecorator(self.view.scaleX.set, self.setInput),
            )
            setattr(
                self.view.scaleY,
                "set",
                absoluteDecorator(self.view.scaleY.set, self.setInput),
            )
            if getExtensionDefault(extensionKey, fallback=None):
                valueX = getExtensionDefault(key_scaleX_points, fallback=None)
                valueY = getExtensionDefault(key_scaleY_points, fallback=None)
                print(valueX, valueY)
                self.view.scaleX.originalSet(str(round(valueX)) if bool(valueX) else "")
                self.view.scaleY.originalSet(str(round(valueY)) if bool(valueY) else "")
            self.setSign(state)


ScaleAbsolutely(extensionKey)
