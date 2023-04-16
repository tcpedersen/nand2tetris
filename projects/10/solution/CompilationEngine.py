import os
import sys

import LexicalElement as le


class CompilationWriter:
    def __init__(self, outputStream):
        self.stream = outputStream
        self.indentlevel = 0

    def write(self, string):
        indent = "    " * self.indentlevel
        self.stream.write(indent + string)

    def writeTerminal(self, element):
        assert isinstance(element, le.LexicalElement)
        self.write(
            f"<{element.xmlLabel()}> {element.xmlTag()} </{elemenet.xmlLabel()}>"
        )

    def writeNonTerminalStart(self, token):
        self.write(f"<{token}>")
        self.indentlevel += 1

    def writeNonTerminalEnd(self, token):
        self.indentlevel -= 1
        self.write(f"</{token}>")


# Rules:
#   1) a compilexxx (except compileClass) statement assumes advance has been called
#      prior to call.
#   2) a compilexxx call will advance to the next token prior to return.
class CompilationEngine:
    def __init__(self, tokenizer, outputStream):
        self.tokenizer = tokenizer
        self.writer = CompilationWriter(outputStream)

    def compileClass(self):
        self.writer.writeNonTerminalStart("class")

        self.tokenizer.advance()
        self.writeTerminal(le.KeyWord, "class")

        # Write className.
        self.tokenizer.advance()
        self.writeTerminal(le.Identifier)

        # Write '{'
        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, "{")

        # Compile body.
        self.tokenizer.advance()
        while True:
            token = self.tokenizer.getTokenType().element

            if token in {"static", "field"}:
                self.compileClassVarDec()
            elif token in {"constructor", "function", "method"}:
                self.compileSubroutine()
            elif token == "}":
                break
            else:
                raise ValueError("something went wrong.")

        # Write '}'
        self.writeTerminal(le.Symbol, "}")

        assert not self.tokenizer.hasMoreTokens()
        self.writer.writeNonTerminalEnd("class")

    def compileClassVarDec(self):
        assert self.tokenizer.tokenType().element in {"static", "field"}
        self.writeTerminal(le.KeyWord)

        # Write type.
        self.tokenizer.advance()
        self.writeTerminal()

        # Write first varName.
        self.tokenizer.advance()
        self.writeTerminal(le.Identifier)

        while True:
            self.tokenizer.advance()
            if self.tokenizer.tokenType().element == ";":
                break

            self.writeTerminal(le.Symbol, ",")

            self.tokenizer.advance()
            self.writeTerminal(le.Identifier)

        self.writeTerminal(le.Symbol, ";")

    def compileSubroutine(self):
        assert self.tokenizer.tokenType().element in {
            "constructor",
            "function",
            "method",
        }
        self.writeTerminal(le.KeyWord)

        # Write type.
        self.tokenizer.advance()
        self.writeTerminal()

        # Write subroutineName.
        self.tokenizer.advance()
        self.writeTerminal(le.Identifier)

        # Write "("
        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, "(")

        # Write parameterList.
        self.compileParamterList()
        self.writeTerminal(le.Symbol, ")")

        # Write subroutine body.
        self.tokenizer.advance()
        while True:
            if self.tokenizer.tokenType().element in {
                "let",
                "if",
                "while",
                "do",
                "return",
            }:
                statements = True
                break

            if self.tokenizer.tokenType().element == "}":
                statements = False
                break

            self.compileVarDec()

        if statements:
            self.compileStatements()

        self.writeTerminal(le.Symbol, "}")

    def compileParameterList(self):
        first = True
        while True:
            if self.tokenizer.tokenType().element not in {
                "int",
                "char",
                "boolean",
            } or not isinstance(self.tokenizer.tokenType(), le.Identifier):
                break

            if first:
                # Write type.
                self.writeTerminal()
                first = False
            else:
                self.writeTerminal(le.Symbol, ",")

                # Write type.
                self.tokenizer.advance()
                self.writeTerminal()

            # Write varName.
            self.tokenizer.advance()
            self.writeTerminal(le.Identifier)

            self.tokenizer.advance()

    def compileVarDec(self):
        self.writeTerminal(le.KeyWord, "var")

        # Write type.
        self.tokenizer.advance()
        self.writeTerminal()

        # Write varName.
        self.tokenizer.advance()
        self.writeTerminal(le.Identifier)

        while True:
            self.tokenizer.advance()
            if self.tokenizer.tokenType().element == ";":
                break

            self.writeTerminal(le.Symbol, ",")

            # Write varName.
            self.tokenizer.advance()
            self.writeTerminal(le.Identifier)

        self.writeTerminal(le.Symbol, ";")
        self.tokenizer.advance()

    def compileStatements(self):
        while True:
            if self.tokenizer.tokenType().element == "let":
                self.compileLet()
            elif self.tokenizer.tokenType().element == "if":
                self.compileIf()
            elif self.tokenizer.tokenType().element == "while":
                self.compileWhile()
            elif self.tokenizer.tokenType().element == "do":
                self.compileDo()
            elif self.tokenizer.tokenType().element == "return":
                self.compileReturn()
            else:
                break

    def compileDo(self):
        self.writeTerminal(le.KeyWord, "do")

        # subroutineName / className / varName
        self.tokenizer.advance()
        self.writeTerminal(le.Identifier)

        self.tokenizer.advance()
        if self.tokenizer.tokenType.elemenet == ".":
            self.writeTerminal(le.Symbol, ".")
            self.tokenizer.advance()

        self.writeTerminal(le.Symbol, "(")

        self.tokenizer.advance()
        self.compileExpressionList()

        self.writeTerminal(le.Symbol, ")")

        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, ";")
        self.tokenizer.advance()

    def compileLet(self):
        self.writeTerminal(le.KeyWord, "let")

        # varName
        self.tokenizer.advance()
        self.writeTerminal(le.Identifier)

        self.tokenizer.advance()
        if self.tokenizer.tokenType().element == "[":
            self.writeTerminal(le.Symbol, "[")

            self.tokenizer.advance()
            self.compileExpression()

            self.writeTerminal(le.Symbol, "]")
            self.tokenizer.advance()

        self.writeTerminal(le.Symbol, "=")

        self.tokenizer.advance()
        self.compileExpression()

        self.writeTerminal(le.Symbol, ";")
        self.tokenizer.advance()

    def compileWhile(self):
        self.writeTerminal(le.KeyWord, "while")

        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, "(")

        self.tokenizer.advance()
        self.compileExpression()

        self.writeTerminal(le.Symbol, ")")

        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, "{")

        self.tokenizer.advance()
        self.compileStatements()

        self.writeTerminal(le.Symbol, "}")
        self.tokenizer.advance()

    def compileReturn(self):
        self.writeTerminal(le.KeyWord, "return")

        self.tokenizer.advance()
        if self.tokenizer.tokenType().element != ";":
            self.compileExpression()

        self.writeTerminal(le.Symbol, ";")
        self.tokenizer.advance()

    def compileIf(self):
        self.writeTerminal(le.KeyWord, "if")

        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, "(")

        self.tokenizer.advance()
        self.compileExpression()

        self.writeTerminal(le.Symbol, ")")

        self.tokenizer.advance()
        self.writeTerminal(le.Symbol, "{")

        self.tokenizer.advance()
        self.compileStatements()

        self.writeTerminal(le.Symbol, "}")
        self.tokenizer.advance()

        if self.tokenizer.tokenType().element == "else":
            self.writeTerminal(le.KeyWord, "else")

            self.tokenizer.advance()
            self.writeTerminal(le.Symbol, "{")

            self.tokenizer.advance()
            self.compileStatement()

            self.writeTerminal(le.Symbol, "}")
            self.tokenizer.advance()

    def compileExpression(self):
        self.compileTerm()

        while self.tokenizer.tokenType().element in {
            "+",
            "-",
            "*",
            "/",
            "&",
            "|",
            "<",
            ">",
            "=",
        }:
            self.writeTerminal(le.Symbol)
            self.compileTerm()

    def compileTerm(self):
        # integerConstant
        if isinstance(self.tokenizer.tokenType(), le.IntegerConstant):
            self.writeTerminal(le.IntegerConstant)
            self.tokenizer.advance()

        # stringConstant
        elif isinstance(self.tokenizer.tokenType(), le.StringConstant):
            self.writeTerminal(le.StringConstant)
            self.tokenizer.advance()

        # keywordConstant
        elif self.tokenizer.tokenType().element in {"true", "false", "null", "this"}:
            self.writeTerminal(le.KeyWord)
            self.tokenizer.advance()

        # unaryOp
        elif self.tokenizer.tokenType().element in {"-", "~"}:
            self.writeTerminal(le.Symbol)
            self.tokenizer.advance()

        # "(" expression ")"
        elif self.tokenizer.tokenType().element == "(":
            self.writeTerminal(le.Symbol, "(")

            self.tokenizer.advance()
            self.compileExpression()

            self.writeTerminal(le.Symbol, ")")
            self.tokenizer.advance()

        else:
            self.writeTerminal(le.Identifier)
            self.tokenizer.advance()

            # varName "[" expression "]"
            if self.tokenizer.tokenType().element == "[":
                self.writeTerminal(le.Symbol, "[")

                self.tokenizer.advance()
                self.compileExpression()

                self.writeTerminal(le.Symbol, "]")
                self.tokenizer.advance()

            # subroutineCall
            elif self.tokenizer.tokenType().element in {"(", "."}:
                # subroutineName / className / varName
                self.tokenizer.advance()
                self.writeTerminal(le.Identifier)

                self.tokenizer.advance()
                if self.tokenizer.tokenType.elemenet == ".":
                    self.writeTerminal(le.Symbol, ".")
                    self.tokenizer.advance()

                self.writeTerminal(le.Symbol, "(")

                self.tokenizer.advance()
                self.compileExpressionList()

                self.writeTerminal(le.Symbol, ")")

                self.tokenizer.advance()

            # varName
            else:
                pass

    def compileExpressionList(self):
        if (
            isinstance(self.tokenizer.tokenType(), le.IntegerConstant)
            or isinstance(self.tokenizer.tokenType(), le.StringConstant)
            or self.tokenizer.tokenType().element in {"true", "false", "null", "this"}
            or isinstance(self.tokenizer.tokenType(), le.Identifier)
            or self.tokenizer.tokenType().element in {"(", "-", "~"}
        ):
            self.compileExpression()
            while True:
                if self.tokenizer.tokenType().element != ",":
                    break
                self.writeTerminal(le.Symbol, ",")
                self.compileExpression()

    def writeTerminal(self, elemType=None, elemVal=None):
        tokenType = self.tokenizer.tokenType()
        if elemType is not None:
            assert isinstance(tokenType, expectedType)
        if elemVal is not None:
            assert tokenType.element == elemVal

        self.writer.writeTerminal(tokenType)
