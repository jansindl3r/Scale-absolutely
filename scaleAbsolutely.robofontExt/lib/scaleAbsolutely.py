import math

from pathlib import Path
from mojo.events import addObserver, clearObservers
from functools import wraps
from lib.UI.roundRectButton import RoundRectButton
from lib.UI.inspector.transformPane import TransformPane
from vanilla import Button, CheckBox
from typing import Callable


def possibleZeroDivison(numr, dnom, result=1.0) -> float:
    """
    it is expected that zero divison can appear. Like when scaling
    a path that has width but no height
    """
    try:
        return numr / dnom
    except ZeroDivisionError:
        return result


def absoluteScaleCallback(self, sender) -> None:
    """
    Absolute point scale callback. It uses the original one,
    But it recalculates the scale based on wanted point width, height.
    """
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
    """
    decorater to modify the default scaleCallback
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> None:
        def newFunc(self, *args, **kwargs) -> None:
            if self.absolutelyBool:
                absoluteScaleCallback(self, *args, **kwargs)
            else:
                func(self, *args, **kwargs)
            return None
        return newFunc(self, *args, **kwargs)
    return wrapper

setattr(TransformPane, "scaleCallback", absoluteDecorator(TransformPane.scaleCallback))
setattr(TransformPane, "absolutelyBool", False)

clearObservers()

class ScaleAbsolutely:
    def __init__(self) -> None:
        addObserver(
            self,
            "inspectorWindowWillShowDescriptions",
            "inspectorWindowWillShowDescriptions",
        )
        with open(Path(__file__).parent/'buttonState.txt', 'r') as inputFile:
            self.buttonState = bool(inputFile.read())

    def setButtonState(self, state: bool) -> None:
        self.buttonState = state
        with open(Path(__file__).parent/'buttonState.txt', 'w+') as outputFile:
            outputFile.write(str(state))

    def scaleAbsolutelyCallback(self, sender) -> None:
        """
        switching state of button globally and notation of input fields
        """
        if sender.get():
            sign = "pt"
            state = True
        else:
            sign = "%"
            state = False

        self.setButtonState(state)
        self.view.absolutelyBool = state
        self.view.scaleYProcent.set(sign)
        self.view.scaleXProcent.set(sign)

    def scaleExistingButtons(self) -> None:
        """
        not in use now, but may be useful later
        """
        buttonsToChange  = ["scaleButton", "scaleTextX", "scaleX", "scaleXProcent", "scaleTextY", "scaleY", "scaleYProcent", "scaleProportional"]
        for i, buttonName in enumerate(buttonsToChange):
            button = getattr(self.view, buttonName)
            left, top, width, height = button.getPosSize()
            if i != 0:
                left *= 0.9
            width *= 0.9
            button.setPosSize((left, top, width, height))


    def inspectorWindowWillShowDescriptions(self, notification) -> None:
        """
        sets the new checkbox and moves the other a bit away
        """
        for subMenu in notification["descriptions"]:
            if subMenu["label"] == "Transform":
                view = subMenu["view"]
                break
        if view:
            left, top, width, height = view.scaleProportional.getPosSize()
            view.scaleProportional.setPosSize((left, math.ceil(top-height/2)+2, width, height))
            view.absolutelyBool = self.buttonState
            scaleAbsolutely = CheckBox(
                (left, math.floor(top+height/2), width, height),
                "pt",
                sizeStyle = "small",
                callback = (self.scaleAbsolutelyCallback),
                value = self.buttonState
            )
            view.scaleAbsolutely = scaleAbsolutely
            self.view = view


ScaleAbsolutely()