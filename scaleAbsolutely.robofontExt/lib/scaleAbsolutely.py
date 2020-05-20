import vanilla
import AppKit
import __main__
import re

from lib.UI.inspector import transformPane
from lib.UI.inspector.transformPane import TransformPane
from mojo.events import addObserver, clearObservers
from lib.UI.roundRectButton import RoundRectButton
from lib.UI.integerEditText import IntegerEditText, BaseNumberEditText
from lib.tools.transformGlyph import TransformGlyph
from typing import Callable, Tuple, Union
from functools import wraps
from mojo.extensions import getExtensionDefault, setExtensionDefault
from tools import EvalUserInput


class ScaleAbsolutely:
    def __init__(self) -> None:
        addObserver(
            self,
            "inspectorWindowWillShowDescriptions",
            "inspectorWindowWillShowDescriptions",
        )
        self.stateDict = {True: "pt", False: "%"}
        self.view: TransformPane = None
        self.lineGap = 34
        self.keys = {
            "setX": "jan-sindler.scale.absolutely.x.set",
            "setY": "jan-sindler.scale.absolutely.y.set",
            "scaleX": "jan-sindler.scale.absolutely.x.points",
            "scaleY": "jan-sindler.scale.absolutely.y.points",
        }

    def possibleZeroDivison(
        self, numr: float, dnom: float, result: float = 0
    ) -> Union[float, int]:
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

    def getSelection(self, glyph) -> list:
        container = []
        for contour in glyph:
            for point in contour.bPoints:
                if point.selected or not glyph.selection:
                    container.append(point)
        return container

    def getBounds(self, selection: tuple) -> Tuple[Tuple[int, ...], ...]:
        """
        gets Current Selection as tuple of points
        if no selection, the whole glyph becomes one
        """
        points = tuple(pt.anchor for pt in selection)
        xMin, _ = min(points, key=lambda x: x[0])
        xMax, _ = max(points, key=lambda x: x[0])
        _, yMin = min(points, key=lambda x: x[1])
        _, yMax = max(points, key=lambda x: x[1])
        return (xMin, xMax), (yMin, yMax)

    def setPosCallback(self, sender) -> None:
        """
        enter callback for set pos button and edit
        """
        glyph = CurrentGlyph()
        transformBox = {
            "bottom": 0,
            "middle": 0.5,
            "top": 1,
            "left": 0,
            "center": 0.5,
            "right": 1,
        }
        box = self.view.transformBox.get()
        box = box if box != "zeroZeroPoint" else "leftBottom"
        currentBox = re.split("(?=[A-Z])", box)
        boxRatios = map(lambda x: transformBox[x.lower()], currentBox)
        fontInfo = CurrentFont().info

        selection = self.getSelection(glyph)
        dimensions = self.getBounds(selection)
        offX, offY = [
            self.interpolate(*dim, ratio) for dim, ratio in zip(dimensions, boxRatios)
        ]

        inputX = EvalUserInput(str(self.view.setPosX.get()), offX, fontInfo).result
        inputY = EvalUserInput(str(self.view.setPosY.get()), offY, fontInfo).result

        for point in selection:
            point.move(
                (
                    inputX - offX if inputX != None else 0,
                    inputY - offY if inputY != None else 0,
                )
            )
        glyph.update()
        setExtensionDefault(self.keys["setX"], inputX)
        setExtensionDefault(self.keys["setY"], inputY)

    def interpolate(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def absScaleCallback(self, sender, x=True, y=True) -> None:
        """
        Absolute point scale callback. It uses the original one,
        But it recalculates the scale based on wanted point width, height.
        """

        (left, right), (bottom, top) = self.getBounds(self.getSelection(CurrentGlyph()))
        curWidth = right - left
        curHeight = top - bottom
        if x:
            valueX = str(self.view.scaleAbsX.get())
            setExtensionDefault(self.keys["scaleX"], valueX)
            valueX = EvalUserInput(valueX, curWidth, CurrentFont().info).result
            _scaleX = self.possibleZeroDivison(valueX, curWidth)
        else:
            _scaleX = 1

        if y:
            valueY = str(self.view.scaleAbsY.get())
            setExtensionDefault(self.keys["scaleY"], valueY)
            valueY = EvalUserInput(valueY, curHeight, CurrentFont().info).result
            _scaleY = self.possibleZeroDivison(valueY, curHeight)
        else:
            _scaleY = 1

        transformDict = dict(scaleX=_scaleX * 100, scaleY=_scaleY * 100)
        self.view._callculateTransformation(transformDict, self.view.glyph)
        self.view._transformMatrixToDefaults()
        self.view._setUndoManagerForGlyphs(
            [self.view.glyph], isinstance(sender, vanilla.Button)
        )

    def additionToGUI_set(self) -> None:
        self.view.setPosButton = RoundRectButton(
            self.view.translateButton.getPosSize(),
            "|Set|:",
            sizeStyle="small",
            callback=(self.setPosCallback),
        )
        self.view.setPosTextX = vanilla.TextBox(
            self.view.translateTextX.getPosSize(), "x:", sizeStyle="small"
        )
        self.view.setPosX = BaseNumberEditText(
            self.view.translateX.getPosSize(),
            getExtensionDefault(self.keys["setX"], fallback=0),
            sizeStyle="small",
            enterCallback=self.setPosCallback,
        )
        self.view.setPosTextY = vanilla.TextBox(
            self.view.translateTextY.getPosSize(), "y:", sizeStyle="small"
        )
        self.view.setPosY = BaseNumberEditText(
            self.view.translateY.getPosSize(),
            getExtensionDefault(self.keys["setY"], fallback=0),
            sizeStyle="small",
            enterCallback=self.setPosCallback,
        )
        self.view.h_0 = vanilla.HorizontalLine(self.view.h1.getPosSize())

    def additionToGUI_scale(self) -> None:
        self.view.scaleAbsButton = RoundRectButton(
            self.view.translateButton.getPosSize(),
            "|Scale|:",
            sizeStyle="small",
            callback=(self.absScaleCallback),
        )
        self.view.scaleAbsTextX = vanilla.TextBox(
            self.view.translateTextX.getPosSize(), "x:", sizeStyle="small"
        )
        self.view.scaleAbsX = BaseNumberEditText(
            self.view.translateX.getPosSize(),
            getExtensionDefault(self.keys["scaleX"], fallback=0),
            sizeStyle="small",
            enterCallback=self.absScaleCallback,
        )
        self.view.scaleAbsTextY = vanilla.TextBox(
            self.view.translateTextY.getPosSize(), "y:", sizeStyle="small"
        )
        self.view.scaleAbsY = BaseNumberEditText(
            self.view.translateY.getPosSize(),
            getExtensionDefault(self.keys["scaleY"], fallback=0),
            sizeStyle="small",
            enterCallback=self.absScaleCallback,
        )
        self.view.h0 = vanilla.HorizontalLine(self.view.h1.getPosSize())

    def shiftOtherGUI(self) -> None:
        for element in dir(self.view):
            if element in ["transformBox", "h0", "h_0"]:
                continue
            if (
                element.startswith("align")
                or element.startswith("flip")
                or element.startswith("set")
                or element.startswith("scaleAbs")
            ):
                continue
            try:
                left, top, width, height = getattr(self.view, element).getPosSize()
                try:
                    getattr(self.view, element).setPosSize(
                        (left, top + self.lineGap, width, height)
                    )
                except Exception as e:
                    print(e)
            except:
                pass

    def inspectorWindowWillShowDescriptions(self, notification) -> None:
        """
        sets the new checkbox and moves the other a bit away
        """
        for subMenu in notification["descriptions"]:
            if subMenu["label"] == "Transform":
                view = subMenu["view"]
                break
        if view:
            self.view = view
            self.additionToGUI_set()
            self.shiftOtherGUI()
            self.additionToGUI_scale()
            self.shiftOtherGUI()

            subMenu["size"] += self.lineGap * 2


if __name__ == "__main__":

    scaleAbsolutely = ScaleAbsolutely()
    __main__.scaleAbsolutely = scaleAbsolutely
