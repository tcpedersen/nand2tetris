import os
import sys
import string
import random

import LexicalElement as le
from SymbolTable import SymbolTable


class CompilationWriter:
    def __init__(self, outputStream):
        self.stream = outputStream
        self.indentlevel = 0

    def write(self, string):
        indent = "    " * self.indentlevel
        self.stream.write(indent + string + "\n")

    def assertTerminal(self, element):
        assert isinstance(element, le.LexicalElement)
        self.write(f"<{element.xmlLabel()}> {element.xmlTag()} </{element.xmlLabel()}>")

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
    def __init__(self, tokenizer, writer):
        self.tokenizer = tokenizer
        self.writer = writer
        self.table = SymbolTable()

        self._className = None

    def compileClass(self):
        self.tokenizer.advance()
        self.assertTerminal(le.Keyword, "class")

        # Save class name.
        self.tokenizer.advance()
        self.assertTerminal(le.Identifier)
        self._className = self.tokenElement()

        # Write '{'
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "{")

        # Compile body.
        self.tokenizer.advance()
        while True:
            token = self.tokenElement()

            if token in {"static", "field"}:
                self.compileClassVarDec()
            elif token in {"constructor", "function", "method"}:
                self.compileSubroutine()
            elif token == "}":
                break
            else:
                raise ValueError("something went wrong.")

        # Write '}'
        self.assertTerminal(le.Symbol, "}")

        assert not self.tokenizer.hasMoreTokens()

    def compileClassVarDec(self):
        self.assertTerminal(le.Keyword)
        varKind = self.tokenElement()
        assert varKind in {"static", "field"}

        # Write type.
        self.tokenizer.advance()
        self.assertTerminal()
        varType = self.tokenElement()

        # Define first variable.
        self.tokenizer.advance()
        self.assertTerminal(le.Identifier)
        varName = self.tokenElement()
        self.table.define(varName, varType, varKind)

        while True:
            self.tokenizer.advance()
            if self.tokenizer.tokenType().element == ";":
                break

            self.assertTerminal(le.Symbol, ",")

            # Define one more variable.
            self.tokenizer.advance()
            self.assertTerminal(le.Identifier)
            varName = self.tokenElement()
            self.table.define(varName, varType, varKind)

        self.assertTerminal(le.Symbol, ";")
        self.tokenizer.advance()

    def compileSubroutine(self):
        self.writer.startSubroutine()

        self.assertTerminal(le.Keyword)
        funcType = self.tokenElement()
        assert funcType in {"constructor", "function", "method"}

        # Get returnType.
        self.tokenizer.advance()
        self.assertTerminal()
        returnType = self.tokenElement()

        # Get subroutineName.
        self.tokenizer.advance()
        self.assertTerminal(le.Identifier)
        subroutineName = self.tokenElement()

        # Generate symbol table.
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "(")

        if funcType == "method":
            self.table.define("this", subroutineName, "arg")

        self.tokenizer.advance()
        self.compileParameterList()

        self.assertTerminal(le.Symbol, ")")
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "{")

        # Compile variable declarations.
        self.tokenizer.advance()
        while True:
            if self.tokenElement() in {"let", "if", "while", "do", "return"}:
                statements = True
                break

            if self.tokenElement() == "}":
                statements = False
                break

            self.compileVarDec()

        # If subroutine is constructor, then allocate memory on the heap.
        if funcType == "constructor":
            self.writer.writePush("constant", self.table.varCount("field"))
            self.writer.writeCall("Memory.alloc", 1)
            self.writer.writePop("pointer", 0)  # Address is returned from memory.allow.

        # If subroutine is method, then allign 'this'.
        if funcType == "method":
            self.writer.writePush("argument", 0)  # 'this' is argument 0.
            self.writer.writePop("pointer", 0)

        # Compile statements.
        if statements:
            self.compileStatements()

        # Return from subroutine.
        self.assertTerminal(le.Symbol, "}")
        self.tokenizer.advance()
        self.writer.writeReturn()

    def compileParameterList(self):
        first = True
        while True:
            if (
                not self.tokenElement() in {"int", "char", "boolean"}
                or isinstance(self.tokenizer.tokenType(), le.Identifier)
                or self.tokenElement() == ","
            ):
                break

            if first:
                # Get type.
                self.assertTerminal()
                varType = self.tokenElement()
                first = False
            else:
                self.assertTerminal(le.Symbol, ",")

                # Get type.
                self.tokenizer.advance()
                self.assertTerminal()
                varType = self.tokenElement()

            # Get varName.
            self.tokenizer.advance()
            self.assertTerminal(le.Identifier)
            varName = self.tokenElement()

            self.table.define(varName, varType, "arg")

            self.tokenizer.advance()

    def compileVarDec(self):
        self.assertTerminal(le.Keyword, "var")

        # Get type.
        self.tokenizer.advance()
        self.assertTerminal()
        varType = self.tokenElement()

        # Get varName.
        self.tokenizer.advance()
        self.assertTerminal(le.Identifier)
        varName = self.tokenElement()

        self.table.define(varName, varType, "var")

        while True:
            self.tokenizer.advance()
            if self.tokenElement() == ";":
                break

            self.assertTerminal(le.Symbol, ",")

            # Get varName.
            self.tokenizer.advance()
            self.assertTerminal(le.Identifier)
            varName = self.tokenElement()

            self.table.define(varName, varType, "var")

        self.assertTerminal(le.Symbol, ";")
        self.tokenizer.advance()

    def compileStatements(self):
        while True:
            if self.tokenElement() == "let":
                self.compileLet()
            elif self.tokenElement() == "if":
                self.compileIf()
            elif self.tokenElement() == "while":
                self.compileWhile()
            elif self.tokenElement() == "do":
                self.compileDo()
            elif self.tokenElement() == "return":
                self.compileReturn()
            else:
                break

    def compileDo(self):
        self.assertTerminal(le.Keyword, "do")

        # subroutineName / className / varName
        self.tokenizer.advance()
        self.assertTerminal(le.Identifier)
        identifierName = self.tokenElement()

        # Handle subroutine call.
        self._compileTerm_HandleSubroutineCall(identifierName)

        # End.
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, ";")
        self.tokenizer.advance()

        # Due to void call, we pop returned element.
        self.writer.writePop("temp", 0)

    def compileLet(self):
        self.assertTerminal(le.Keyword, "let")

        # varName
        self.tokenizer.advance()
        self.assertTerminal(le.Identifier)
        varName = self.tokenElement()

        isArrExpr = False

        self.tokenizer.advance()
        if self.tokenizer.tokenType().element == "[":
            # Push base address of array onto stack.
            self.writer.writePush(
                self.table.kindOf(varName), self.table.indexOf(varName)
            )

            # Compute offset of array.
            self.assertTerminal(le.Symbol, "[")

            self.tokenizer.advance()
            self.compileExpression()

            self.assertTerminal(le.Symbol, "]")
            self.tokenizer.advance()

            # Add the two together.
            self.writer.writeArithmetic("add")

            isArrExpr = True

        self.assertTerminal(le.Symbol, "=")

        self.tokenizer.advance()
        self.compileExpression()

        self.assertTerminal(le.Symbol, ";")
        self.tokenizer.advance()

        if isArrExpr:
            self.writer.writePop("temp", 0)  # Store value of rhs.
            self.writer.writePop("pointer", 1)  # Set 'that' to address of lhs.

            self.writer.writePush("temp", 0)  # Push rhs to stack.
            self.writer.writePop("that", 0)  # Store rhs in 'that'.
        else:
            self.writer.writePop(
                self.table.kindOf(varName), self.table.indexOf(varName)
            )

    def compileWhile(self):
        self.assertTerminal(le.Keyword, "while")

        # Define two unique labels.
        uniqueLabel = "".join(random.choices(string.ascii_uppercase, k=8))
        whileBeginLabel = "WHILE_BEGIN." + uniqueLabel
        whileEndLabel = "WHILE_END." + uniqueLabel

        # Mark beginning of while loop.
        self.writer.writeLabel(whileBeginLabel)

        # Compile while expression.
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "(")

        self.tokenizer.advance()
        self.compileExpression()

        self.assertTerminal(le.Symbol, ")")

        # Negate result.
        self.writer.writeArithmetic("neg")

        # Jump to end of while loop.
        self.writer.writeIf(whileEndLabel)

        # Compile statements.
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "{")

        self.tokenizer.advance()
        self.compileStatements()

        self.assertTerminal(le.Symbol, "}")
        self.tokenizer.advance()

        # Jump to begining of while loop.
        self.writer.writeGoto(whileBeginLabel)

        # Mark end of while loop.
        self.writer.writeLabel(whileEndLabel)

    def compileReturn(self):
        self.assertTerminal(le.Keyword, "return")

        self.tokenizer.advance()
        if self.tokenizer.tokenType().element != ";":
            self.compileExpression()

        self.assertTerminal(le.Symbol, ";")
        self.tokenizer.advance()

        self.writer.writeReturn()

    def compileIf(self):
        self.assertTerminal(le.Keyword, "if")

        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "(")

        # Compile expression.
        self.tokenizer.advance()
        self.compileExpression()

        self.assertTerminal(le.Symbol, ")")

        # Negate result.
        self.writer.writeArithmetic("neg")

        # Generate two unique labels.
        uniqueLabel = "".join(random.choices(string.ascii_uppercase, k=8))
        isFalseLabel = "ISFALSE.{uniqueLabel}"
        isTrueLabel = "ISTRUE.{uniqueLabel}"

        # If false, skip statements.
        self.writer.writeIf(isFalseLabel)

        # Compile 'if' statements.
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "{")

        self.tokenizer.advance()
        self.compileStatements()

        self.assertTerminal(le.Symbol, "}")
        self.tokenizer.advance()

        # Skip else statements.
        self.writer.writeGoto(isTrueLabel)

        # Mark beginning of 'else' statement.
        self.writer.writeLabel(isFalseLabel)

        # Compile 'else' statement.
        if self.tokenizer.tokenType().element == "else":
            self.assertTerminal(le.Keyword, "else")

            self.tokenizer.advance()
            self.assertTerminal(le.Symbol, "{")

            self.tokenizer.advance()
            self.compileStatements()

            self.assertTerminal(le.Symbol, "}")
            self.tokenizer.advance()

        # Mark label to skip else statement.
        self.writer.writeLabel(isTrueLabel)

    def compileExpression(self):
        self.compileTerm()

        while self.tokenElement() in {"+", "-", "*", "/", "&", "|", "<", ">", "="}:
            # Get operator.
            self.assertTerminal(le.Symbol)
            operator = self.tokenizer.tokenElement()

            self.tokenizer.advance()
            self.compileTerm()

            # Invoke operator.
            if operator == "*":
                self.writer.writeCall("Math.multiply", 2)
            elif operator == "/":
                self.writer.writeCall("Math.divide", 2)
            else:
                translation = {
                    "+": "add",
                    "-": "sub",
                    "&": "and",
                    "|": "or",
                    "<": "lt",
                    ">": "gt",
                    "=": "eq",
                }
                self.writer.writeArithmetic(translation[operator])

    def _compileTerm_HandleIntegerConstant(self):
        self.assertTerminal(le.IntegerConstant)
        self.writer.writePush("constant", self.tokenizer.intVal())
        self.tokenizer.advance()

    def _compileTerm_HandleStringConstant(self):
        self.assertTerminal(le.StringConstant)

        # Find length of string.
        string = self.tokenElement()
        length = len(string)

        # Allocate memory on the heap.
        self.writer.writePush("constant", length)
        self.writer.writeCall("String.new", 1)

        # Fill string.
        for char in string:
            self.writer.writePush("constant", ord(char))
            self.writer.writeCall("String.appendChar", 2)

        self.tokenizer.advance()

    def _compileTerm_HandleKeywordConstant(self):
        self.assertTerminal(le.Keyword)

        # Push variable.
        if self.tokenElement() in {"false", "null"}:
            self.writer.push("constant", 0)
        elif self.tokenElement() in {"true"}:
            self.writer.push("constant", 1)
            self.writer.writeArithmetic("neg")
        else:
            self.writer.push("argument", 0)  # push this

        self.tokenizer.advance()

    def _compileTerm_HandleUnaryOp(self):
        self.assertTerminal(le.Symbol)
        self.tokenizer.advance()

        self.compileTerm()
        self.writer.writeArithmetic("neg")

    def _compileTerm_HandleParenthesisExpression(self):
        self.assertTerminal(le.Symbol, "(")

        self.tokenizer.advance()
        self.compileExpression()

        self.assertTerminal(le.Symbol, ")")
        self.tokenizer.advance()

    def _compileTerm_HandleArrayIndexing(self, arrayName):
        # Push base address of array.
        self.writePush(self.table.kindOf(arrayName), self.table.indexOf(arrayName))

        # Evaluate expression.
        self.assertTerminal(le.Symbol, "[")

        self.tokenizer.advance()
        self.compileExpression()

        self.assertTerminal(le.Symbol, "]")
        self.tokenizer.advance()

        # Add the two together.
        self.writer.writeArithmetic("add")

        # Reallocate 'that' to correct address.
        self.writer.writePop("pointer", 1)

        # Push contents of array entry onto stack.
        self.writer.writePush("that", 0)  # TODO should this be 'this'?

    def _compileTerm_HandleSubroutineCall(self, identifierName):
        nArgs = 0
        if self.tokenElement() == ".":
            self.assertTerminal(le.Symbol, ".")

            # The name of the scoped subroutine.
            self.tokenizer.advance()
            self.assertTerminal(le.Identifier)

            if self.table.kindOf(identifierName) is None:
                # Is a function / constructor call.
                continue
            else:
                # Is a method call for some other object.
                self._compileTerm_HandleVariable(identifierName)
                nArgs += 1

            subroutineName = identifierName + "." + self.tokenElement()
        else:
            # Is a method call for the current object.
            self.writer.writePush("argument", 0)  # Must contain this.
            subroutineName = self._className + "." + identifierName
            nArgs += 1

        # Push explicit arguments onto stack.
        self.tokenizer.advance()
        self.assertTerminal(le.Symbol, "(")

        self.tokenizer.advance()
        nArgs += self.compileExpressionList()

        self.assertTerminal(le.Symbol, ")")

        # Call subroutine.
        self.writer.writeCall(subroutineName, nArgs)

        self.tokenizer.advance()

    def _compileTerm_HandleVariable(self, identifierName):
        varNameKind = self.kindOf(identifierName)
        varNameIndex = self.indexOf(identifierName)
        translation = {
            "static": "static",
            "field": "this",
            "arg": "argument",
            "var": "local",
        }

        self.writer.writePush(translation[varNameKind], varNameIndex)

        # Do not advance, since caller will have advanced one too far.

    def compileTerm(self):
        # integerConstant
        if isinstance(self.tokenizer.tokenType(), le.IntegerConstant):
            self._compileTerm_HandleIntegerConstant()

        # stringConstant
        elif isinstance(self.tokenizer.tokenType(), le.StringConstant):
            self._compileTerm_HandleStringConstant()

        # keywordConstant
        elif self.tokenElement() in {"true", "false", "null", "this"}:
            self._compileTerm_HandleKeywordConstant()

        # unaryOp
        elif self.tokenElement() in {"-", "~"}:
            self._compileTerm_HandleKeywordConstant()

        # "(" expression ")"
        elif self.tokenElement() == "(":
            self._compileTerm_HandleParanthesisExpression()

        else:
            # Get (beginning of) identifier  name.
            self.assertTerminal(le.Identifier)
            identifierName = self.tokenElement()

            # Peek...
            self.tokenizer.advance()

            # varName "[" expression "]"
            if self.tokenElement() == "[":
                self._compileTerm_HandleArrayIndexing(identifierName)

            # subroutineCall
            elif self.tokenElement() in {"(", "."}:
                self._compileTerm_HandleSubroutineCall(identifierName)

            # varName
            else:
                self._compileTerm_HandleVariable(identifierName)

    def compileExpressionList(self):
        nArgs = 0
        if (
            isinstance(self.tokenType(), le.IntegerConstant)
            or isinstance(self.tokenType(), le.StringConstant)
            or self.tokenElement() in {"true", "false", "null", "this"}
            or isinstance(self.tokenType(), le.Identifier)
            or self.tokenElement() in {"(", "-", "~"}
        ):
            self.compileExpression()
            nArgs += 1

            while True:
                if self.tokenElement() != ",":
                    break

                self.assertTerminal(le.Symbol, ",")
                self.tokenizer.advance()

                self.compileExpression()
                nArgs += 1

        # Return number of expressions.
        return nArgs

    def assertTerminal(self, elemType=None, elemVal=None):
        tokenType = self.tokenizer.tokenType()
        if elemVal is not None:
            assert (
                tokenType.element == elemVal
            ), f"element is '{tokenType.element}', not '{elemVal}'."
        if elemType is not None:
            assert isinstance(tokenType, elemType), (
                f"tokenType '{tokenType.element}' is '{tokenType.__class__.__name__}', "
                "not '{elemType.__name__}'."
            )

    def tokenElement(self):
        return self.tokenizer.tokenType().element

    def tokenType(self):
        return self.tokenizer.tokenType()
