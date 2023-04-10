import re

class TokenType:
    def __init__(self, tokentype):
        self._validateTokenType(tokentype)
        self.tokentype = tokentype

    def _validateTokenType(self, tokentype):
        allowedTokenTypes = [
            "KEYWORD",
            "SYMBOL",
            "IDENTIFIER",
            "INT_CONST",
            "STRING_CONST",
        ]
        if tokentype not in allowedTokenTypes:
            raise TypeError(f"tokentype {tokentype} is not valid.")

class KeyWord:
    def __init__(self, keyword):
        self._validateKeyWord(keyword)
        self.keyword = keyword

    def _validateKeyWord(self, keyword):
        allowedKeyWords = [
            "class",
            "method",
            "function",
            "constructor",
            "int",
            "boolean",
            "char",
            "void",
            "var",
            "static",
            "field",
            "let",
            "do",
            "if",
            "else",
            "while",
            "return",
            "true",
            "false",
            "null",
            "this",
        ]
        if keyword not in allowedKeyWords:
            raise TypeError(f"keyword {keyword} is not valid.")

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
        regex = r"^.*(//.*)$"
        line = re.sub(regex, str(), line)

        # Remove standard comments.
        regex = r"^.*(\/\*.*\*\/).*$"
        line = re.sub(regex, str(), line)

        # Strips the line.
        line = line.strip()

        return line

class JackTokenizer:
    def __init__(self, stream):
        self.stream = stream
        self._token = None
        self._currentline = None

        # Generate the jack lines.
        self._lines = []
        for line in self.stream.readlines():
            jackline = JackLine(line.rstrip("\n"))
            if not jackline.isEmpty():
                self._lines.append(jackline)

    def hasMoreTokens(self):
        return bool(self._lines) or not self._currentline.isEmpty()

    def advance(self):
        if self._currentline is None or self._currentline.isEmpty():
            self._currentline = self._lines.pop(0)
        self._token = self._currentline.pop()

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

