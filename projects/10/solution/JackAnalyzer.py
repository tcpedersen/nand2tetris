import sys
import os
import glob
import pathlib

from JackTokenizer import JackTokenizer

class JackAnalyzer:
    def __init__(self, inputStream):
        self.inputStream = inputStream

def handleFile(inputfile):
    # Assert that filepath points to a jack file.
    if pathlib.Path(inputfile).suffix != ".jack":
        raise ValueError("invalid filetype of input file.")

    # Create path for output file.
    outputfile = inputfile.replace(".jack", ".xml")

    return [(inputfile, outputfile)]

def handleDirectory(folderpath):
    ret = []
    for path in glob.glob(os.path.join(folderpath, "*.jack")):
        ret.extend(handleFile(path))

    return ret

def getIOPaths(path):
    if os.path.isfile(path):
        paths = handleFile(path)
    elif os.path.isdir(path):
        paths = handleDirectory(path)

    return paths

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError('invalid number of arguments provided.')

    # Create input and output files.
    paths = getIOPaths(sys.argv[1])

    for inputfile, outputfile in paths:
        print(f"Tokenizing file {inputfile}.")
        with open(inputfile, 'r') as inputstream:
            tokenizer = JackTokenizer(inputstream)

            while tokenizer.hasMoreTokens():
                tokenizer.advance()
                print(tokenizer._token)






