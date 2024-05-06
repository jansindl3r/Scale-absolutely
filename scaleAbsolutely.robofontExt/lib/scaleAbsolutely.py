import vanilla
import AppKit
import __main__
import re

from lib.UI.roundRectButton import RoundRectButton
from lib.UI.inspector.transformPane import TransformBox
from lib.UI.integerEditText import BaseNumberEditText
from typing import Tuple, Union
from mojo.extensions import getExtensionDefault, setExtensionDefault
from tools import EvalUserInput
from mojo.subscriber import Subscriber, registerRoboFontSubscriber
from vanilla import TextBox, Group, HorizontalStackGroup

transformBox = {
    "bottom": 0,
    "middle": 0.5,
    "top": 1,
    "left": 0,
    "center": 0.5,
    "right": 1,
}

class ScaleAbsolutely(Subscriber):

    debug = True
    default_keys = {
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
    
    @property
    def origin(self):
        box = self.view.transform_box.get()
        box = box if box != "zeroZeroPoint" else "leftBottom"
        currentBox = re.split("(?=[A-Z])", box)
        currentBoxY, currentBoxX = currentBox
        currentBoxY = currentBoxY.lower()
        currentBoxX = currentBoxX.lower()
        return [transformBox[currentBoxX], transformBox[currentBoxY]]

    def setPosCallback(self, sender) -> None:
        """
        enter callback for set pos button and edit
        """
        glyph = CurrentGlyph()

        fontInfo = CurrentFont().info

        selection = self.getSelection(glyph)
        dimensions = self.getBounds(selection)
        offX, offY = [
            self.interpolate(*dim, ratio) for dim, ratio in zip(dimensions, self.origin)
        ]

        inputX = EvalUserInput(str(self.view.set_row.set_x.get()), offX, fontInfo).result
        inputY = EvalUserInput(str(self.view.set_row.set_y.get()), offY, fontInfo).result

        for point in selection:
            point.move(
                (
                    inputX - offX if inputX != None else 0,
                    inputY - offY if inputY != None else 0,
                )
            )
        glyph.update()
        setExtensionDefault(self.default_keys["setX"], inputX)
        setExtensionDefault(self.default_keys["setY"], inputY)

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
            valueX = str(self.view.scale_row.scale_x.get())
            setExtensionDefault(self.default_keys["scaleX"], valueX)
            valueX = EvalUserInput(valueX, curWidth, CurrentFont().info).result
            _scaleX = self.possibleZeroDivison(valueX, curWidth)
        else:
            _scaleX = 1
 
        if y:
            valueY = str(self.view.scale_row.scale_y.get())
            setExtensionDefault(self.default_keys["scaleY"], valueY)
            valueY = EvalUserInput(valueY, curHeight, CurrentFont().info).result
            _scaleY = self.possibleZeroDivison(valueY, curHeight)
        else:
            _scaleY = 1

        transformDict = (_scaleX, 0, 0, _scaleY, 0, 0)
        
        glyph = CurrentGlyph()
        origin_x, origin_y = self.origin
        selection = self.getSelection(glyph)
        for point in selection:
            point.transformBy(transformDict, origin=(
                left + origin_x * curWidth,
                bottom + origin_y * curHeight
                )
            )
        glyph.update()


    def build(self):
        group = Group((0, 0, -0, -0))

        group.transform_box = TransformBox((10, 10, 40, 40))

        group.set_row = HorizontalStackGroup((70, 10, -10, 20))
        group.set_row.set_button = RoundRectButton((0, 0, 50, 20), "|Set|", sizeStyle="small", callback=self.setPosCallback)
        group.set_row.x_label = TextBox((60, 0, 20, 20), "x:", sizeStyle="small")
        group.set_row.set_x = BaseNumberEditText((80, 0, 50, 20), getExtensionDefault(self.default_keys["setX"], fallback=0), sizeStyle="small")
        group.set_row.y_label = TextBox((140, 0, 20, 20), "y:", sizeStyle="small")
        group.set_row.set_y = BaseNumberEditText((160, 0, 50, 20), getExtensionDefault(self.default_keys["setY"], fallback=0), sizeStyle="small")

        group.scale_row = HorizontalStackGroup((70, 30, -10, 20))
        group.scale_row.scale_button = RoundRectButton((0, 0, 50, 20), "|Scale|", sizeStyle="small", callback=self.absScaleCallback)
        group.scale_row.x_label = TextBox((60, 0, 20, 20), "x:", sizeStyle="small")
        group.scale_row.scale_x = BaseNumberEditText((80, 0, 50, 20), getExtensionDefault(self.default_keys["scaleX"], fallback=0), sizeStyle="small")
        group.scale_row.y_label = TextBox((140, 0, 20, 20), "y:", sizeStyle="small")
        group.scale_row.scale_y = BaseNumberEditText((160, 0, 50, 20), getExtensionDefault(self.default_keys["scaleY"], fallback=0), sizeStyle="small")

        return group


    def roboFontWantsInspectorViews(self, info):

        self.view = self.build()
        item = dict(label="Scale, Absolutely!", view=self.view, size=60, canResize=False)

        transform_pane_index = 0
        for i, pane in enumerate(info["viewDescriptions"]):
            if pane.get("label") == "Transform":
                transform_pane_index = i
                break
        info["viewDescriptions"].insert(transform_pane_index, item)


if __name__ == "__main__":
    registerRoboFontSubscriber(ScaleAbsolutely)

