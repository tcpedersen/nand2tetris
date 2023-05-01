import re
import LexicalElement


class JackLine:
    def __init__(self, line=str()):
        self.line = self._cleanLine(line)

    def isEmpty(self):
        return self.line == "" or re.match(r"^\s*$", self.line) is not None

    def pop(self):
        element = self.line[0]
        self.line = self.line[1:]

        return element

    def peek(self):
        return self.line[0]

    def _cleanLine(self, line):
        # Remove comments to end of line.
        regex = r"(//.*)"
        line = re.sub(regex, str(), line)

        # Remove standard comments.
        regex = r"^.*(\/\*.*\*\/).*$"
        line = re.sub(regex, str(), line)

        # Strips the line.
        line = line.strip()

        return line


class JackTokenizer:
    def __init__(self, stream):
        self._token = None
        self._currentline = None
        self._currentlineNumber = 0
        self._lines = self._cleanCode(stream.read())

    def _cleanCode(self, code):
        # Remove standard and API comments.
        regex = r"(/\*\*.*?\*/)"
        code = re.sub(regex, str(), code, flags=re.DOTALL)

        # Split into JackLine objects.
        return [
            jackline
            for jackline in [JackLine(line) for line in code.split("\n")]
            if not jackline.isEmpty()
        ]

    def hasMoreTokens(self):
        return bool(self._lines) or not self._currentline.isEmpty()

    def advance(self):
        if self._currentline is None or self._currentline.isEmpty():
            self._currentline = self._lines.pop(0)
            self._currentlineNumber += 1
        self._token = self._getNextToken()

    def _getNextToken(self):
        # Pop until next token is not whitespace. We can ignore trailing
        # whitespace as JackLine guarantees no such thing.
        token = self._currentline.pop()
        while token == " ":
            token = self._currentline.pop()

        # If token is symbol, then we are done.
        if LexicalElement.Symbol.isvalid(token):
            return token

        insideString = token == '"'

        # Keep adding to buffer until we hit a whitespace, symbol, or EOL.
        peek = self._currentline.peek()
        while True:
            if not insideString:
                if LexicalElement.Symbol.isvalid(peek) or peek == " ":
                    break
            else:
                if len(token) > 1 and token[-1] == '"':
                    break

            token += self._currentline.pop()
            if self._currentline.isEmpty():
                break
            peek = self._currentline.peek()

        return token

    def tokenType(self):
        if LexicalElement.Keyword.isvalid(self._token):
            return LexicalElement.Keyword(self._token)
        if LexicalElement.Symbol.isvalid(self._token):
            return LexicalElement.Symbol(self._token)
        if LexicalElement.IntegerConstant.isvalid(self._token):
            return LexicalElement.IntegerConstant(self._token)
        if LexicalElement.StringConstant.isvalid(self._token):
            return LexicalElement.StringConstant(self._token)
        if LexicalElement.Identifier.isvalid(self._token):
            return LexicalElement.Identifier(self._token)

        raise ValueError(
            f"token '{self._token}' found in line {self._currentlineNumber} is invalid."
        )

    def xmlTag(self):
        return self.tokenType().xmlTag()

    def xmlLabel(self):
        return self.tokenType().xmlLabel()

    def keyWord(self):
        return LexicalElement.Keyword(self._token).element

    def symbol(self):
        return LexicalElement.Symbol(self._token).element

    def identifier(self):
        return LexicalElemenet.Identifier(self._token).element

    def intVal(self):
        return int(LexicalElement.IntegerConstant(self._token).element)

    def stringVal(self):
        return LexicalElemenet.StringConstant(self._token).element
