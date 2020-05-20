import __main__

scaleAbsolutely = getattr(__main__, 'scaleAbsolutely', None)
assert scaleAbsolutely

def runSize(x: bool, y: bool) -> None:
    scaleFunc = getattr(scaleAbsolutely, 'absScaleCallback', None)
    assert scaleFunc
    scaleFunc(None, x, y)