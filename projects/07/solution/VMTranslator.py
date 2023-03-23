import sys
import pathlib

from parser import Parser, CommandType
from codewriter import CodeWriter

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError('invalid number of arguments provided.')

    inputFileName = sys.argv[1]
    outputFileName = inputFileName.replace('.vm', '.asm')

    with open(inputFileName, 'r') as inputStream:
        with open(outputFileName, 'w') as outputStream:
            parser = Parser(inputStream)
            codewriter = CodeWriter(outputStream)
            
            codewriter.setFileName(pathlib.Path(inputFileName).stem)

            while parser.hasMoreCommands():
                parser.advance() 

                if parser.commandType() == CommandType.C_ARITHMETIC:
                    codewriter.writeArithmetic(parser.arg1())

                if parser.commandType() == CommandType.C_PUSH:
                    codewriter.writePushPop('push', parser.arg1(), parser.arg2())

                if parser.commandType() == CommandType.C_POP:
                    codewriter.writePushPop('pop', parser.arg1(), parser.arg2())

