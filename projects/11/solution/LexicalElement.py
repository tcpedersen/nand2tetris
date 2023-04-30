import re


class LexicalElement:
    def __init__(self, element):
        self.element = element

    @staticmethod
    def isvalid(element):
        raise NotImplementedError("children must overwrite this method.")

    def xmlTag(self):
        return self.element

    def xmlLabel(self):
        return type(self).__name__[0].lower() + type(self).__name__[1:]


class Keyword(LexicalElement):
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
            "~",
        ]

        return element in allowed

    def xmlTag(self):
        if self.element == "<":
            return "&lt;"
        if self.element == ">":
            return "&gt;"
        if self.element == "&":
            return "&amp;"
        return super().xmlTag()


class IntegerConstant(LexicalElement):
    def isvalid(element):
        try:
            return 0 <= int(element) < 2**15
        except ValueError:
            return False


class StringConstant(LexicalElement):
    def isvalid(element):
        return re.match(r"\".+\"", element) is not None

    def xmlTag(self):
        match = re.match(r"\"(.+)\"", self.element)
        return match.group(1)


class Identifier(LexicalElement):
    def isvalid(element):
        if element[0].isdigit():
            return False
        return re.match(r"\w+", element, flags=re.ASCII) is not None
