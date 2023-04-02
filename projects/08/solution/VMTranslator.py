import sys
import os
import pathlib
import glob

from parser import Parser, CommandType
from codewriter import CodeWriter


def writeBootstrapCode(outputStream):
    codewriter = CodeWriter(outputStream)
    codewriter.writeInit()


def assemble(inputFileName, outputStream):
    # Instantiate codewriter.
    codewriter = CodeWriter(outputStream)
    codewriter.setFileName(pathlib.Path(inputFileName).stem)

    with open(inputFileName, 'r') as inputStream:
        parser = Parser(inputStream)

        while parser.hasMoreCommands():
            parser.advance() 
            if parser.commandType() == CommandType.C_ARITHMETIC:
                codewriter.writeArithmetic(parser.arg1())

            if parser.commandType() == CommandType.C_PUSH:
                codewriter.writePushPop('push', parser.arg1(), parser.arg2())

            if parser.commandType() == CommandType.C_POP:
                codewriter.writePushPop('pop', parser.arg1(), parser.arg2())
            
            if parser.commandType() == CommandType.C_LABEL:
                codewriter.writeLabel(parser.arg1())

            if parser.commandType() == CommandType.C_GOTO:
                codewriter.writeGoto(parser.arg1())

            if parser.commandType() == CommandType.C_IF:
                codewriter.writeIf(parser.arg1())

            if parser.commandType() == CommandType.C_CALL:
                codewriter.writeCall(parser.arg1(), parser.arg2())

            if parser.commandType() == CommandType.C_RETURN:
                codewriter.writeReturn()

            if parser.commandType() == CommandType.C_FUNCTION:
                codewriter.writeFunction(parser.arg1(), parser.arg2())



if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError('invalid number of arguments provided.')

    inputArgument = sys.argv[1]
    if os.path.isfile(inputArgument):
        if pathlib.Path(inputArgument).suffix != '.vm':
            raise ValueError('invalid filetype of input file.')
        inputFiles = [inputArgument]
        outputFileName = inputArgument.replace('.vm', '.asm')
        writeBootstrap = False
    elif os.path.isdir(inputArgument):
        inputFiles = glob.glob(os.path.join(inputArgument, '*.vm'))
        mainFileName = os.path.basename(os.path.normpath(inputArgument))
        outputFileName = os.path.join(inputArgument, f'{mainFileName}.asm')
        writeBootstrap = True

    print(f"Input files: {inputFiles}")
    print(f"Output files: {outputFileName}")

    with open(outputFileName, 'w') as outputStream:
        if writeBootstrap:
            print("Generating bootstrap code.")
            writeBootstrapCode(outputStream)

        for inputFileName in inputFiles:
            print(f"Assembling {inputFileName}")
            assemble(inputFileName, outputStream)

