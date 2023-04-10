import re

from LexicalElement import Symbol

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
        self._token = self._getNextToken()

    def _getNextToken(self):
        token = self._currentline.pop()

        # Pop until next token is not whitespace.
        while token == " ":
            token = self._currentline.pop()

        # If token is symbol, then we are done.
        if Symbol.isvalid(token):
            return token

        # Keep adding to buffer until we hit a whitespace, symbol, or EOL.
        peek = self._currentline.peek()
        while not Symbol.isvalid(peek) and peek != " ":
            token += self._currentline.pop()
            if self._currentline.isEmpty():
                break
            peek = self._currentline.peek()

        return token

    def tokenType(self):
        return TokenType("KEYWORD")

    def keyWord(self):
        return KeyWord("CLASS")

    def symbol(self):
        return str()

    def identifier(self):
        return str()

    def intVal(self):
        return int()

    def stringVal(self):
        return str()

