from mojo.events import addObserver, clearObservers
from functools import wraps
from lib.UI.roundRectButton import RoundRectButton
from lib.UI.inspector.transformPane import TransformPane
from vanilla import Button, CheckBox
from typing import Callable


def possibleZeroDivison(numr, dnom, result=1.0) -> float:
    try:
        return numr / dnom
    except ZeroDivisionError:
        return result


def absoluteScaleCallback(self, sender) -> None:
    glyph = CurrentGlyph()
    pointObjects = (
        glyph.selection
        if glyph.selection
        else (c.segments for c in glyph)
    )
    points = tuple(pt.position for pt in pointObjects)
    xMin, _ = min(points, key=lambda x: x[0])
    xMax, _ = max(points, key=lambda x: x[0])
    _, yMin = min(points, key=lambda x: x[1])
    _, yMax = max(points, key=lambda x: x[1])

    curWidth, curHeight = xMax - xMin, yMax - yMin
    _scaleX = possibleZeroDivison(self.scaleX.get(), curWidth)
    _scaleY = possibleZeroDivison(self.scaleY.get(), curHeight)

    transformDict = dict(scaleX=_scaleX * 100, scaleY=_scaleY * 100)
    self._callculateTransformation(transformDict, self.glyph)
    self._transformMatrixToDefaults()
    self._setUndoManagerForGlyphs([self.glyph], isinstance(sender, Button))


def absoluteDecorator(func) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Callable:
        def newFunc(self, *args, **kwargs) -> None:
            if self.absolutelyBool:
                absoluteScaleCallback(self, *args, **kwargs)
            else:
                func(self, *args, **kwargs)

        return newFunc(self, *args, **kwargs)

    return wrapper


setattr(TransformPane, "scaleCallback", absoluteDecorator(TransformPane.scaleCallback))
setattr(TransformPane, "absolutelyBool", False)


class ScaleAbsolutely:
    def __init__(self) -> None:
        addObserver(
            self,
            "inspectorWindowWillShowDescriptions",
            "inspectorWindowWillShowDescriptions",
        )

    def scaleAbsolutelyCallback(self, sender) -> None:
        if sender.get():
            sign = "pt"
            self.view.absolutelyBool = True

        else:
            sign = "%"
            self.view.absolutelyBool = False

        self.view.scaleYProcent.set(sign)
        self.view.scaleXProcent.set(sign)

    def inspectorWindowWillShowDescriptions(self, notification) -> None:
        for subMenu in notification["descriptions"]:
            if subMenu["label"] == "Transform":
                view = subMenu["view"]
                break
        if view:
            left, top, width, height = view.scaleProportional.getPosSize()
            scaleAbsolutely = CheckBox(
                (left + width, top, width, height),
                "pt",
                sizeStyle="small",
                callback=(self.scaleAbsolutelyCallback),
            )
            view.scaleAbsolutely = scaleAbsolutely
            self.view = view


ScaleAbsolutely()
