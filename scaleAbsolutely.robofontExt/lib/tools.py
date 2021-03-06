from typing import Union
from lib.fontObjects.fontPartsWrappers import CurrentFont
import re


class EvalUserInput(object):
    """
    Evaluates user's input and calculates it if formula provided.
    If not formula is provided, it returns none, so other way has to be
    used to convert user's input into float or int
    """

    zones = [
        "postscriptBlueValues",
        "postscriptOtherBlues",
        "postscriptFamilyBlues",
        "postscriptFamilyOtherBlues",
    ]

    def __init__(
        self, userInput: str, curSize: Union[float, int], fontInfo: CurrentFont
    ) -> None:
        pattern = re.compile(r"^([0-9\.]+)+$")
        match = re.match(pattern, userInput)
        if len(userInput) == 0:
            self.result = curSize
        elif match:
            self.result = float(userInput)
        else:
            self.userInput = str(userInput)
            self.curSize = curSize
            self.fontInfo = fontInfo
            self.variables = self.getVariables()
            self.result = round(self.evalUserInput())

    def getVariables(self, zones: list=zones) -> dict:
        container: list = []
        for zone in zones:
            container += getattr(self.fontInfo, zone)

        zoneDict = {}
        for vals in zip(container[::2], container[1:][::2]):
            k, v = sorted(vals, key=lambda x: abs(x))
            zoneDict[k] = v

        variables = {
            "x": self.fontInfo.xHeight,
            "c": self.fontInfo.capHeight,
            "d": self.fontInfo.descender,
            "a": self.fontInfo.ascender,
        }

        for k, v in [i for i in variables.items()]:
            value = zoneDict.get(v, v)
            variables[k.upper()] = value

        variables.setdefault("B", zoneDict.get(0, 0))

        return variables

    def evalUserInput(self) -> Union[float, int]:
        operators = ("*", "/", "+", "-", "%")
        formula = self.userInput
        for operator in operators:
            if formula.startswith(operator):
                formula = str(self.curSize) + formula
        for key in self.variables.keys():
            if key in formula:
                formula = formula.replace(key, str(abs(self.variables[key])))
        out = eval(formula)
        return out

