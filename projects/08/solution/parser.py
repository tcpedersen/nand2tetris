class CommandType:
    C_ARITHMETIC = 0
    C_PUSH = 1
    C_POP = 2
    C_LABEL = 3
    C_GOTO = 4
    C_IF = 5
    C_FUNCTION = 6
    C_RETURN = 7
    C_CALL = 8


class Parser:
    def __init__(self, stream):
        self.stream = stream
        self.currentCommand = None

    def hasMoreCommands(self):
        currentPos = self.stream.tell()
        line = self.stream.readline()
        self.stream.seek(currentPos)

        return bool(line)

    def advance(self):
        self.currentCommand = self.stream.readline().rstrip('\n')

        if self._isComment(self.currentCommand) or self._isEmptyLine(
            self.currentCommand
        ):
            self.advance()

    def _isComment(self, line):
        return line.strip().startswith(r"//")

    def _isEmptyLine(self, line):
        return line == ""

    def _rawCommandType(self):
        return self.currentCommand.split()[0]

    def _rawArg1(self):
        return self.currentCommand.split()[1]

    def _rawArg2(self):
        return self.currentCommand.split()[2]

    def commandType(self):
        cmd = self._rawCommandType()

        # Arithmetic / logical commands.
        if cmd in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return CommandType.C_ARITHMETIC

        # Memory access commands.
        if cmd == "push":
            return CommandType.C_PUSH
        if cmd == "pop":
            return CommandType.C_POP

    def arg1(self):
        if self.commandType() == CommandType.C_RETURN:
            raise ValueError("cannot handle C_RETURN command type.")
        if self.commandType() == CommandType.C_ARITHMETIC:
            return self._rawCommandType()

        return self._rawArg1()

    def arg2(self):
        if self.commandType() in [
            CommandType.C_PUSH,
            CommandType.C_POP,
            CommandType.C_FUNCTION,
            CommandType.C_CALL,
        ]:
            return int(self._rawArg2())
        raise ValueError("invalid command type.")

