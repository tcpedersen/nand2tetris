import random

SEGMENT_POINTERS = {
    'local': 'LCL',
    'argument': 'ARG',
    'this': 'THIS',
    'that': 'THAT',
}

BOOLEANS = {
    'true': -1,
    'false': 0,
}

class CodeWriterGenericOperations:
    def __init__(self, write):
        self.write = write

    def popFromStackToDRegister(self):
        self.decrementStackPointer()
        self.write("@SP")
        self.write("A=M")
        self.write("D=M")

    def pushFromDRegisterToStack(self):
        self.pushFromDRegisterToAddress("SP")
        self.incrementStackPointer()

    def incrementStackPointer(self):
        self.write("@SP")
        self.write("M=M+1")

    def decrementStackPointer(self):
        self.write("@SP")
        self.write("M=M-1")

    def popFromStackToAddressInDRegister(self):
        self.write("@pop.addr")
        self.write("M=D")

        self.popFromStackToDRegister()
        self.pushFromDRegisterToAddress("pop.addr")

    # I.e. *ADDR = D
    def pushFromDRegisterToAddress(self, address):
        self.write(f"@{address}")
        self.write("A=M")
        self.write("M=D")

    # I.e. ADDR = D
    def changeAddressToDRegister(self, address):
        self.write(f"@{address}")
        self.write("M=D")


class CodeWriter:
    def __init__(self, stream):
        self.stream = stream
        self._labelCounter = 0
        self.fileName = None
        self._genericops = CodeWriterGenericOperations(self._write)
        self._currentFunction = None
        self._indent = 0

    # ===== Public methods =============================================================
    def setFileName(self, fileName):
        self.fileName = fileName
        self._write(f"// === {fileName} =====")
        self._indent = 1

    def writeArithmetic(self, command):
        self._write(rf'// {command}')

        if command == 'add':
            return self._add()
        if command == 'sub':
            return self._sub()
        if command == 'neg':
            return self._neg()

        if command == 'eq':
            return self._eq()
        if command == 'gt':
            return self._gt()
        if command == 'lt':
            return self._lt()

        if command == 'and':
            return self._and()
        if command == 'or':
            return self._or()
        if command == 'not':
            return self._not()

        raise ValueError('invalid command.')

    def writePushPop(self, command, segment, index):
        self._write(rf'// {command} {segment} {index}')

        if segment in ['local', 'argument', 'this', 'that']:
            return self._pushPopGeneric(command, segment, index)
        if segment == 'constant':
            return self._pushConstant(index)
        if segment == 'temp':
            return self._pushPopTemp(command, index)
        if segment == 'pointer':
            return self._pushPopPointer(command, index)
        if segment == 'static':
            return self._pushPopStatic(command, index)

    def writeInit(self):
        self._write("// Bootstrap code")
        self._currentFunction = "bootstrap"
        self._indent = 1

        # Initialise stack pointer.
        self._write("@256")
        self._write("D=A")
        self._genericops.changeAddressToDRegister("SP")

        # Call Sys.init.
        self.writeCall("Sys.init", 0)

        self._currentFunction = None
        self._indent = 0

    def writeLabel(self, label):
        self._write(rf'// label {label}')

        funcLabel = self._getFunctionLabel(label)
        self._write(f"({funcLabel})")

    def writeGoto(self, label):
        self._write(rf'// goto {label}')

        funcLabel = self._getFunctionLabel(label)
        self._write(f"@{funcLabel}")
        self._write("0;JMP")

    def writeIf(self, label):
        self._write(rf'// if-goto {label}')

        funcLabel = self._getFunctionLabel(label)
        self._genericops.popFromStackToDRegister()
        self._write(f"@{funcLabel}")
        self._write("D;JNE")

    def writeCall(self, functionName, numArgs):
        self._write(rf'// call {functionName} {numArgs}')

        returnAddr = self._getFunctionReturnLabel()
        self._write(f"@{returnAddr}")
        self._write("D=A")
        self._genericops.pushFromDRegisterToStack()

        # Save frame to stack.
        for label in ["LCL", "ARG", "THIS", "THAT"]:
            self._write(f"@{label}")
            self._write("D=M")
            self._genericops.pushFromDRegisterToStack()

        # Reposition ARG.
        adj = numArgs + 5
        self._write("@SP")
        self._write("D=M")
        self._write(f"@{adj}")
        self._write("D=D-A")
        self._genericops.changeAddressToDRegister("ARG")

        # Reposition LCL.
        self._write("@SP")
        self._write("D=M")
        self._genericops.changeAddressToDRegister("LCL")

        # goto f
        self._write(f"@{functionName}")
        self._write("0;JMP")

        self._write(f"({returnAddr})")

    def writeReturn(self):
        self._write(rf'// return')

        def repositionLabelFromFrameOffset(address, offset):
            self._write(f"@{offset}")
            self._write("D=A")
            self._write("@FRAME")
            self._write("A=M-D")
            self._write("D=M")
            self._genericops.changeAddressToDRegister(address)

        # FRAME = LOCAL
        self._write("@LCL")
        self._write("D=M")
        self._genericops.changeAddressToDRegister("FRAME")

        # RET = *(FRAME - 5)
        repositionLabelFromFrameOffset("RET", 5)

        # *ARG = pop()
        self._genericops.popFromStackToDRegister()
        self._genericops.pushFromDRegisterToAddress("ARG")
        
        # SP = ARG+1
        self._write("@ARG")
        self._write("D=M+1")
        self._genericops.changeAddressToDRegister("SP")

        repositionLabelFromFrameOffset("THAT", 1)
        repositionLabelFromFrameOffset("THIS", 2)
        repositionLabelFromFrameOffset("ARG", 3)
        repositionLabelFromFrameOffset("LCL", 4)

        # goto RET
        self._write(f"@RET")
        self._write("A=M")
        self._write("0;JMP")

    def writeFunction(self, functionName, numLocals):
        self._write(rf'// function {functionName} {numLocals}')
        self._currentFunction = functionName

        self._write(f"({functionName})")
        for k in range(numLocals):
            self.writePushPop("push", "constant", 0)

    # === Private methods ==============================================================
    def _write(self, line):
        indent = "    " * self._indent
        self.stream.write(indent + line + '\n')

    def _add(self):
        self._genericops.popFromStackToDRegister()

        # Replace stack element with sum.
        self._write("@SP")
        self._write("A=M-1")
        self._write("M=M+D")

    def _sub(self):
        self._genericops.popFromStackToDRegister()

        # Replace stack element with sub.
        self._write("@SP")
        self._write("A=M-1")
        self._write("M=M-D")

    def _neg(self):
        self._write("@SP")
        self._write("A=M-1")
        self._write("M=-M")

    def _comparisonTemplate(self, jumpCommand):
        self._genericops.popFromStackToDRegister()
        uniqueId = self._labelCounter

        self._write("@SP")
        self._write("A=M-1")
        self._write("D=M-D")

        self._write(f"@IS_TRUE.{uniqueId}")
        self._write(f"D;{jumpCommand}")

        # IS_FALSE
        self._write("@SP")
        self._write("A=M-1")
        self._write(f"M={BOOLEANS['false']}")

        self._write(f"@END_OF_CMD.{uniqueId}")
        self._write("0;JMP")

        # IS_TRUE
        self._write(f"(IS_TRUE.{uniqueId})")
        self._write("@SP")
        self._write("A=M-1")
        self._write(f"M={BOOLEANS['true']}")

        self._write(f"(END_OF_CMD.{uniqueId})")

        self._labelCounter += 1

    def _eq(self):
        self._comparisonTemplate("JEQ")

    def _gt(self):
        self._comparisonTemplate("JGT")

    def _lt(self):
        self._comparisonTemplate("JLT")

    def _and(self):
        self._genericops.popFromStackToDRegister()

        # Replace stack element with and.
        self._write("@SP")
        self._write("A=M-1")
        self._write("M=D&M")

    def _or(self):
        self._genericops.popFromStackToDRegister()

        # Replace stack element with or.
        self._write("@SP")
        self._write("A=M-1")
        self._write("M=D|M")

    def _not(self):
        self._write("@SP")
        self._write("A=M-1")
        self._write("M=!M")

    def _getSegmentPointer(self, segment):
        return SEGMENT_POINTERS[segment]

    # === Generic ===
    def _pushGeneric(self, segment, index):
        segmentPointer = self._getSegmentPointer(segment)
        self._write(f"@{segmentPointer}")
        self._write("D=M")
        self._write(f"@{index}")
        self._write("A=D+A")
        self._write("D=M")

        self._genericops.pushFromDRegisterToStack()

    def _popGeneric(self, segment, index):
        segmentPointer = self._getSegmentPointer(segment)
        self._write(f"@{segmentPointer}")
        self._write("D=M")
        self._write(f"@{index}")
        self._write("D=D+A")

        self._genericops.popFromStackToAddressInDRegister()

    def _pushPopGeneric(self, command, segment, index):
        if command == 'push':
            return self._pushGeneric(segment, index)
        if command == 'pop':
            return self._popGeneric(segment, index)

    # === Temp ===
    def _pushTemp(self, index):
        self._write(f"@5")
        self._write("D=A")
        self._write(f"@{index}")
        self._write("A=D+A")
        self._write("D=M")

        self._genericops.pushFromDRegisterToStack()

    def _popTemp(self, index):
        self._write(f"@5")
        self._write("D=A")
        self._write(f"@{index}")
        self._write("D=D+A")

        self._genericops.popFromStackToAddressInDRegister()

    def _pushPopTemp(self, command, index):
        if command == 'push':
            return self._pushTemp(index)
        if command == 'pop':
            return self._popTemp(index)

    # === Constant ===
    def _pushConstant(self, index):
        self._write(f"@{index}")
        self._write(f"D=A")
        self._genericops.pushFromDRegisterToStack()

    # === Pointer ===
    def _pushPointer(self, index):
        segmentPointer = self._getSegmentPointer('that' if index else 'this')
        self._write(f"@{segmentPointer}")
        self._write(f"D=M")
        self._genericops.pushFromDRegisterToStack()

    def _popPointer(self, index):
        segmentPointer = self._getSegmentPointer('that' if index else 'this')
        self._write(f"@{segmentPointer}")
        self._write(f"D=A")
        self._genericops.popFromStackToAddressInDRegister()

    def _pushPopPointer(self, command, index):
        if command == 'push':
            return self._pushPointer(index)
        if command == 'pop':
            return self._popPointer(index)

    # === Static ===
    def _pushStatic(self, index):
        varName = f"{self.fileName}.{index}"
        self._write(f"@{varName}")
        self._write("D=M")
        self._genericops.pushFromDRegisterToStack()

    def _popStatic(self, index):
        varName = f"{self.fileName}.{index}"
        self._write(f"@{varName}")
        self._write("D=A")
        self._genericops.popFromStackToAddressInDRegister()

    def _pushPopStatic(self, command, index):
        if command == 'push':
            return self._pushStatic(index)
        if command == 'pop':
            return self._popStatic(index)

    def _getFunctionReturnLabel(self):
        uniqueId = ''.join(random.choice('0123456789ABCDEF') for n in range(8))
        return f"{self._currentFunction}.return-address.{uniqueId}"

    def _getFunctionLabel(self, label):
        return f"{self._currentFunction}${label}"

