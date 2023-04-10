class TokenType:
    KEYWORD = 0
    SYMBOL = 1
    IDENTIFIER = 2
    INT_CONST = 3
    STRING_CONST = 4

class LexicalElement:
    def __init__(self, element):
        if not self.isvalid(element):
            raise ValueError(f"element {element} is not a valid element.")
        self.element = element

    @staticmethod
    def isvalid(element):
        raise NotImplementedError("children must overwrite this method.")

class KeyWord(LexicalElement):
    def isvalid(element):
        allowed = [
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

        return element in allowed

class Symbol(LexicalElement):
    def isvalid(element):
        allowed = [
           "{",
           "}",
           "(",
           ")",
           "[",
           "]",
           ".",
           ",",
           ";",
           "+",
           "-",
           "*",
           "/",
           "&",
           "|",
           "<",
           ">",
           "=",
           "_",
        ]

        return element in allowed

class IntegerConstant(LexicalElement):
    def isvalid(element):
        try:
            return 0 <= int(element) < 2**15
        except ValueError:
            return False

class StringConstant(LexicalElement):
    def isvalid(element):
        return True

class Identifier(LexicalElement):
    def isvalid(element):
        if element[0].isdigit():
            return False
        return re.match(r"\w+", element, flags=re.ASCII) is not None

