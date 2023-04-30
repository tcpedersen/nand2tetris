class VMWriter:
    def __init__(self, stream):
        self.stream = stream

    def write(self, string):
        self.stream.write(string + "\n")

    def writePush(self, segment, index):
        self.write(f"push {segment} {index}")

    def writePop(self, segment, index):
        self.write(f"pop {segment} {index}")

    def writeArithmetic(self, command):
        assert command in {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
        self.write(command)

    def writeLabel(self, label):
        self.write(f"label {label}")

    def writeGoto(self, label):
        self.write(f"goto {label}")

    def writeIf(self, label):
        self.write(f"if-goto {label}")

    def writeCall(self, name, nArgs):
        self.write(f"call {name} {nArgs}")

    def writeFunction(self, name, nLocals):
        self.write(f"function {name} {nLocals}")

    def writeReturn(self):
        self.write("return")
