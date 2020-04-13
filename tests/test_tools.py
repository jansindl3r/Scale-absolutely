from fontParts.world import OpenFont
import unittest
from collections import namedtuple

import sys
sys.path.append("./../scaleAbsolutely.robofontExt/lib")
import tools
from importlib import reload
reload(tools)
import tools

from pathlib import Path

# overshoot = 20

class TestTools(unittest.TestCase):

    def test_inputInteger(self):
        self.assertEqual(tools.EvalUserInput('10', 100, CurrentFont().info), None)

    def test_inputFloat(self):
        self.assertEqual(tools.EvalUserInput('10.1', 100, CurrentFont().info), None)

    def test_adding(self):
        self.assertEqual(tools.EvalUserInput('+10', 100, CurrentFont().info), 110)

    def test_verticalMetricsVars(self):
        self.assertEqual(tools.EvalUserInput('a', 100, CurrentFont().info), 750)

    def test_verticalMetricsVarsWithZones(self):
        self.assertEqual(tools.EvalUserInput('A+B', 100, CurrentFont().info), 790)

    def test_formula(self):
        formula = '(10*A-700-B)-D'
        self.assertEqual(tools.EvalUserInput(formula, 100, CurrentFont().info), 6710) 

    def test_dictionary(self):
        info = CurrentFont().info
        Instance = namedtuple('EvaluserInput', 'fontInfo')
        instance = Instance(info)
        getVariables = tools.EvalUserInput.getVariables
        dictionary = getVariables(instance)
        comparedDictionary = dict(
            d=-250,
            D=-270,
            B=-20,
            x=500,
            X=520,
            c=700,
            C=720,
            a=750,
            A=770,
        )
        self.assertEqual(dictionary, comparedDictionary)


if __name__ == '__main__':
    curFont = CurrentFont()
    path = Path('test_font.ufo')
    if Path(curFont.path).absolute() != path.absolute():
        OpenFont(path)
    loader = unittest.TestLoader()
    tests = []
    for _, obj in list(locals().items()):
        try:
            if issubclass(obj, unittest.TestCase):            
                tests.append(loader.loadTestsFromTestCase(obj))    
        except:
            pass
    suite = unittest.TestSuite(tests)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    print(result)