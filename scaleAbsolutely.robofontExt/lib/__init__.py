import __main__
from scaleAbsolutely import ScaleAbsolutely, extensionKey

def runExtension():
    extension = ScaleAbsolutely(extensionKey)
    with open('file.txt', 'w+') as outputFile:
        outputFile.write(str(id(extension)))
    setattr(__main__, 'scaleAbsolutelyExtension', extension)
    return extension

global extension
extension = runExtension()
